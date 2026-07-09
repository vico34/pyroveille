const LEAFLET_JS = "/pyroveille_static/leaflet.js";
const LEAFLET_CSS = "/pyroveille_static/leaflet.css";

class PyroVeilleMapCard extends HTMLElement {
  setConfig(config) {
    this.config = {
      title: "PyroVeille",
      height: "420px",
      entity_prefix: "device_tracker.pyroveille_",
      entities: [],
      show_hotspots: true,
      show_projections: true,
      show_satellite_zones: true,
      show_aircraft: true,
      ...config,
    };
    if (!this.shadowRoot) {
      this.attachShadow({ mode: "open" });
    }
    this.shadowRoot.innerHTML = `
      <link rel="stylesheet" href="${LEAFLET_CSS}">
      <style>
        :host { display: block; }
        ha-card { overflow: hidden; }
        .header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 12px 16px;
          font-size: 16px;
          font-weight: 600;
        }
        .map {
          height: ${this.config.height};
          min-height: 260px;
          background: #18201a;
        }
        .empty {
          display: grid;
          place-items: center;
          height: 180px;
          color: var(--secondary-text-color);
          font-size: 14px;
          padding: 16px;
          text-align: center;
        }
        .marker {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          display: grid;
          place-items: center;
          position: relative;
          color: #fff;
          font: 700 13px Arial, sans-serif;
          border: 2px solid #fff;
          box-shadow: 0 1px 6px rgba(0, 0, 0, 0.45);
        }
        .marker.fire { background: #e53935; }
        .marker.inactive { background: #757575; }
        .marker.hotspot {
          width: 18px;
          height: 18px;
          background: #d84315;
          border-width: 1px;
        }
        .marker.projection {
          width: 34px;
          height: 34px;
          background: #fb8c00;
          border-color: #263238;
        }
        .marker.aircraft {
          width: 34px;
          height: 34px;
          background: #1976d2;
          border-color: #ffffff;
        }
        .marker.aircraft.heli { background: #00897b; }
        .marker.aircraft.canadair { background: #039be5; }
        .marker.aircraft .arrow {
          width: 0;
          height: 0;
          border-left: 7px solid transparent;
          border-right: 7px solid transparent;
          border-bottom: 18px solid #ffffff;
          transform-origin: 50% 60%;
        }
        .marker.aircraft .label {
          position: absolute;
          bottom: -15px;
          left: 50%;
          transform: translateX(-50%);
          min-width: 24px;
          padding: 1px 4px;
          border-radius: 8px;
          background: rgba(0, 0, 0, 0.72);
          color: #fff;
          font-size: 10px;
          line-height: 12px;
          white-space: nowrap;
        }
        .leaflet-container {
          font-family: var(--primary-font-family, Arial, sans-serif);
        }
      </style>
      <ha-card>
        <div class="header">
          <span>${this.config.title}</span>
        </div>
        <div class="map"></div>
      </ha-card>
    `;
    this.mapElement = this.shadowRoot.querySelector(".map");
    this.map = undefined;
    this.layers = undefined;
  }

  set hass(hass) {
    this._hass = hass;
    this._ensureLeaflet()
      .then(() => this._renderMap())
      .catch((error) => this._showError(error));
  }

  getCardSize() {
    return 5;
  }

  async _ensureLeaflet() {
    if (window.L) {
      return;
    }
    if (!window.pyroVeilleLeafletPromise) {
      window.pyroVeilleLeafletPromise = new Promise((resolve, reject) => {
        const script = document.createElement("script");
        script.src = LEAFLET_JS;
        script.async = true;
        script.onload = resolve;
        script.onerror = () => reject(new Error(`Impossible de charger ${LEAFLET_JS}`));
        document.head.appendChild(script);
      });
    }
    await window.pyroVeilleLeafletPromise;
    if (!window.L) {
      throw new Error("Leaflet n'est pas disponible apres chargement.");
    }
  }

  _renderMap() {
    if (!this._hass || !window.L || !this.mapElement) {
      return;
    }
    if (!this.map) {
      this.map = window.L.map(this.mapElement, {
        zoomControl: true,
        attributionControl: true,
      });
      window.L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap",
      }).addTo(this.map);
      this.layers = window.L.layerGroup().addTo(this.map);
      setTimeout(() => this.map.invalidateSize(), 0);
    }

    this.mapElement.querySelector(".empty")?.remove();
    this.layers.clearLayers();
    const bounds = [];
    const entities = this._pyroVeilleEntities();
    const drawnZones = new Set();

    for (const [entityId, state] of entities) {
      const attrs = state.attributes || {};
      if (this.config.show_satellite_zones) {
        this._drawSatelliteZone(attrs, bounds, drawnZones);
        if (attrs.satellite_zone?.geojson) {
          this._drawGeoJson(attrs.satellite_zone.geojson, bounds, drawnZones);
        }
      }
    }
    for (const [entityId, state] of entities) {
      const attrs = state.attributes || {};
      if (this._isHotspot(entityId, attrs) && this.config.show_hotspots) {
        this._drawMarker(attrs, bounds, "hotspot", "", state);
      } else if (this._isProjection(entityId, attrs) && this.config.show_projections) {
        this._drawMarker(attrs, bounds, "projection", attrs.projection_label || "+", state);
      } else if (this._isAircraft(entityId, attrs) && this.config.show_aircraft) {
        this._drawAircraftTrack(attrs, bounds);
        this._drawAircraftMarker(attrs, bounds, state);
      } else if (this._isFire(entityId, attrs)) {
        this._drawMarker(attrs, bounds, attrs.fire_status === "inactive" ? "inactive" : "fire", "F", state);
        if (this.config.show_satellite_zones && attrs.satellite_zone?.geojson) {
          this._drawGeoJson(attrs.satellite_zone.geojson, bounds, drawnZones);
        }
      }
    }

    if (bounds.length) {
      this.map.fitBounds(bounds, { padding: [24, 24], maxZoom: this.config.default_zoom || 12 });
    } else {
      this._showEmpty();
    }
  }

  _showEmpty() {
    if (!this.mapElement || this.mapElement.querySelector(".empty")) {
      return;
    }
    const empty = document.createElement("div");
    empty.className = "empty";
    empty.textContent = "Aucune entite PyroVeille avec coordonnees n'est disponible pour le moment.";
    this.mapElement.appendChild(empty);
  }

  _showError(error) {
    if (!this.mapElement) {
      return;
    }
    this.mapElement.innerHTML = `<div class="empty">Carte PyroVeille indisponible : ${error.message}</div>`;
  }

  _pyroVeilleEntities() {
    const explicitEntities = new Set(this.config.entities || []);
    return Object.entries(this._hass.states)
      .filter(([entityId, state]) => entityId.startsWith("device_tracker."))
      .filter(([entityId, state]) => {
        const attrs = state.attributes || {};
        return explicitEntities.has(entityId)
          || entityId.startsWith(this.config.entity_prefix)
          || this._hasPyroVeilleAttributes(attrs);
      });
  }

  _hasPyroVeilleAttributes(attrs) {
    return attrs.fire_status != null
      || attrs.projection === true
      || attrs.satellite_hotspot === true
      || attrs.satellite_zone === true
      || attrs.satellite_zone?.geojson != null
      || attrs.geojson != null
      || attrs.aircraft === true
      || attrs.track_geojson != null
      || attrs.hotspot_id != null
      || attrs.projection_label != null
      || attrs.mode === "satellite_hotspots";
  }

  _isFire(entityId, attrs = {}) {
    return (attrs.fire_status != null || entityId.includes("pyroveille_fire_"))
      && !this._isProjection(entityId, attrs)
      && !this._isSatelliteZone(entityId, attrs)
      && !this._isHotspot(entityId, attrs)
      && !this._isAircraft(entityId, attrs);
  }

  _isProjection(entityId, attrs = {}) {
    return entityId.includes("_projection_") || attrs.projection === true || attrs.projection_label != null;
  }

  _isHotspot(entityId, attrs = {}) {
    return entityId.includes("pyroveille_hotspot_") || attrs.satellite_hotspot === true || attrs.hotspot_id != null;
  }

  _isSatelliteZone(entityId, attrs) {
    return entityId.endsWith("_satellite_zone") || attrs.satellite_zone === true || attrs.mode === "satellite_hotspots";
  }

  _isAircraft(entityId, attrs = {}) {
    return entityId.includes("pyroveille_aircraft_") || attrs.aircraft === true || attrs.aircraft_id != null;
  }

  _drawSatelliteZone(attrs, bounds, drawnZones) {
    if (attrs.geojson) {
      this._drawGeoJson(attrs.geojson, bounds, drawnZones);
    }
    const latitude = this._number(attrs.latitude);
    const longitude = this._number(attrs.longitude);
    if (Number.isFinite(latitude) && Number.isFinite(longitude)) {
      bounds.push([latitude, longitude]);
    }
  }

  _drawGeoJson(geojson, bounds, drawnZones) {
    const key = this._geoJsonKey(geojson);
    if (drawnZones?.has(key)) {
      return;
    }
    drawnZones?.add(key);
    const layer = window.L.geoJSON(geojson, {
      style: {
        color: "#d84315",
        weight: 2,
        opacity: 0.85,
        fillColor: "#ff7043",
        fillOpacity: 0.28,
      },
    }).addTo(this.layers);
    const layerBounds = layer.getBounds();
    if (layerBounds.isValid()) {
      bounds.push(layerBounds.getSouthWest());
      bounds.push(layerBounds.getNorthEast());
    }
  }

  _drawAircraftTrack(attrs, bounds) {
    const geojson = attrs.track_geojson;
    if (!geojson) {
      return;
    }
    const color = this._aircraftColor(attrs);
    const layer = window.L.geoJSON(geojson, {
      style: {
        color,
        weight: 3,
        opacity: 0.82,
      },
    }).addTo(this.layers);
    const layerBounds = layer.getBounds();
    if (layerBounds.isValid()) {
      bounds.push(layerBounds.getSouthWest());
      bounds.push(layerBounds.getNorthEast());
    }
  }

  _drawMarker(attrs, bounds, markerClass, label, state) {
    const latitude = this._number(attrs.latitude);
    const longitude = this._number(attrs.longitude);
    if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
      return;
    }
    const icon = window.L.divIcon({
      className: "",
      html: `<div class="marker ${markerClass}">${label}</div>`,
      iconSize: [36, 36],
      iconAnchor: [18, 18],
    });
    const marker = window.L.marker([latitude, longitude], { icon }).addTo(this.layers);
    marker.bindPopup(this._popupContent(state));
    bounds.push([latitude, longitude]);
  }

  _drawAircraftMarker(attrs, bounds, state) {
    const latitude = this._number(attrs.latitude);
    const longitude = this._number(attrs.longitude);
    if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
      return;
    }
    const heading = this._number(attrs.heading) || 0;
    const category = attrs.aircraft_type || attrs.category;
    const markerType = category === "heli" ? "heli" : category === "canadair" ? "canadair" : "";
    const label = this._escapeHtml(attrs.callsign || attrs.registration || attrs.aircraft_id || "A");
    const icon = window.L.divIcon({
      className: "",
      html: `<div class="marker aircraft ${markerType}"><div class="arrow" style="transform: rotate(${heading}deg)"></div><div class="label">${label}</div></div>`,
      iconSize: [38, 46],
      iconAnchor: [19, 19],
    });
    const marker = window.L.marker([latitude, longitude], { icon }).addTo(this.layers);
    marker.bindPopup(this._popupContent(state));
    bounds.push([latitude, longitude]);
  }

  _aircraftColor(attrs) {
    const category = attrs.aircraft_type || attrs.category;
    if (category === "heli") {
      return "#00897b";
    }
    if (category === "canadair") {
      return "#039be5";
    }
    return "#1976d2";
  }

  _number(value) {
    const number = Number(value);
    return Number.isFinite(number) ? number : undefined;
  }

  _geoJsonKey(geojson) {
    return JSON.stringify(geojson?.geometry?.coordinates || geojson);
  }

  _popupContent(state) {
    const attrs = state.attributes || {};
    const name = this._escapeHtml(attrs.friendly_name || state.entity_id);
    const distance = attrs.distance_km != null ? `<br>Distance: ${attrs.distance_km} km` : "";
    const status = attrs.fire_status ? `<br>Statut: ${attrs.fire_status}` : "";
    const radius = attrs.estimated_radius_m ? `<br>Rayon estime: ${attrs.estimated_radius_m} m` : "";
    const aircraftType = this._escapeHtml(attrs.category_label || attrs.aircraft_type || "aeronef");
    const aircraft = attrs.aircraft ? `<br>Type: ${aircraftType}` : "";
    const speed = attrs.speed_kmh != null ? `<br>Vitesse: ${attrs.speed_kmh} km/h` : "";
    const altitude = attrs.altitude_m != null ? `<br>Altitude: ${attrs.altitude_m} m` : "";
    return `<strong>${name}</strong>${status}${distance}${radius}${aircraft}${speed}${altitude}`;
  }

  _escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }
}

if (!customElements.get("pyroveille-map-card")) {
  customElements.define("pyroveille-map-card", PyroVeilleMapCard);
}

window.customCards = window.customCards || [];
if (!window.customCards.some((card) => card.type === "pyroveille-map-card")) {
  window.customCards.push({
    type: "pyroveille-map-card",
    name: "PyroVeille Map Card",
    description: "Carte PyroVeille avec incendies, projections, hotspots, zones satellite FIRMS et moyens aeriens.",
  });
}
