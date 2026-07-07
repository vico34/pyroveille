const LEAFLET_JS = "/pyroveille_static/leaflet.js";
const LEAFLET_CSS = "/pyroveille_static/leaflet.css";

class PyroVeilleMapCard extends HTMLElement {
  setConfig(config) {
    this.config = {
      title: "PyroVeille",
      height: "420px",
      entity_prefix: "device_tracker.pyroveille_",
      show_hotspots: true,
      show_projections: true,
      show_satellite_zones: true,
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
    const entities = Object.entries(this._hass.states)
      .filter(([entityId]) => entityId.startsWith(this.config.entity_prefix));

    for (const [entityId, state] of entities) {
      const attrs = state.attributes || {};
      if (this._isSatelliteZone(entityId, attrs)) {
        this._drawSatelliteZone(attrs, bounds);
      }
    }
    for (const [entityId, state] of entities) {
      const attrs = state.attributes || {};
      if (this._isHotspot(entityId) && this.config.show_hotspots) {
        this._drawMarker(attrs, bounds, "hotspot", "", state);
      } else if (this._isProjection(entityId) && this.config.show_projections) {
        this._drawMarker(attrs, bounds, "projection", attrs.projection_label || "+", state);
      } else if (this._isFire(entityId)) {
        this._drawMarker(attrs, bounds, attrs.fire_status === "inactive" ? "inactive" : "fire", "F", state);
        if (this.config.show_satellite_zones && attrs.satellite_zone?.geojson) {
          this._drawGeoJson(attrs.satellite_zone.geojson, bounds);
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

  _isFire(entityId) {
    return entityId.includes("pyroveille_fire_")
      && !this._isProjection(entityId)
      && !this._isSatelliteZone(entityId, {});
  }

  _isProjection(entityId) {
    return entityId.includes("_projection_");
  }

  _isHotspot(entityId) {
    return entityId.includes("pyroveille_hotspot_");
  }

  _isSatelliteZone(entityId, attrs) {
    return entityId.endsWith("_satellite_zone") || attrs.satellite_zone === true;
  }

  _drawSatelliteZone(attrs, bounds) {
    if (!this.config.show_satellite_zones) {
      return;
    }
    if (attrs.geojson) {
      this._drawGeoJson(attrs.geojson, bounds);
    }
    if (Number.isFinite(attrs.latitude) && Number.isFinite(attrs.longitude)) {
      bounds.push([attrs.latitude, attrs.longitude]);
    }
  }

  _drawGeoJson(geojson, bounds) {
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

  _drawMarker(attrs, bounds, markerClass, label, state) {
    const latitude = attrs.latitude;
    const longitude = attrs.longitude;
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

  _popupContent(state) {
    const attrs = state.attributes || {};
    const name = attrs.friendly_name || state.entity_id;
    const distance = attrs.distance_km != null ? `<br>Distance: ${attrs.distance_km} km` : "";
    const status = attrs.fire_status ? `<br>Statut: ${attrs.fire_status}` : "";
    const radius = attrs.estimated_radius_m ? `<br>Rayon estime: ${attrs.estimated_radius_m} m` : "";
    return `<strong>${name}</strong>${status}${distance}${radius}`;
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
    description: "Carte PyroVeille avec incendies, projections, hotspots et zones satellite FIRMS.",
  });
}
