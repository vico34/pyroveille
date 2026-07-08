"""Device tracker entities for map display."""

from __future__ import annotations

from urllib.parse import quote

from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.components.device_tracker.const import SourceType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import slugify

from .const import DOMAIN
from .coordinator import FeuxDeForetDataCoordinator
from .entity import FeuxDeForetEntity
from .models import AircraftPosition, FireAlert, FireHotspot, FireProjection
from .util import destination_point

_ACTIVE_FIRE_COLOR = "#e53935"
_INACTIVE_FIRE_COLOR = "#757575"
_PROJECTION_COLOR = "#fb8c00"
_HOTSPOT_COLOR = "#d84315"
_AIRCRAFT_COLOR = "#1976d2"
_HELICOPTER_COLOR = "#00897b"
_PROJECTION_STEPS = (0.25, 0.5, 0.75, 1.0)


def _format_projection_label(hours: float) -> str:
    """Return a compact time label for projection markers."""
    if hours <= 0:
        return "+0h"

    rounded_hours = round(hours)
    if abs(hours - rounded_hours) < 0.05:
        return f"+{rounded_hours}h"

    whole_hours = int(hours)
    minutes = round((hours - whole_hours) * 60)
    if minutes == 60:
        return f"+{whole_hours + 1}h"
    if whole_hours <= 0:
        return f"+{minutes}m"
    return f"+{whole_hours}h{minutes:02d}"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up fire trackers."""
    coordinator: FeuxDeForetDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    platform = FireTrackerPlatform(coordinator, async_add_entities)
    entry.async_on_unload(coordinator.async_add_listener(platform.async_update_entities))
    platform.async_update_entities()


class FireTrackerPlatform:
    """Maintain one tracker entity per nearby fire."""

    def __init__(
        self,
        coordinator: FeuxDeForetDataCoordinator,
        async_add_entities: AddEntitiesCallback,
    ) -> None:
        """Initialize platform helper."""
        self._coordinator = coordinator
        self._async_add_entities = async_add_entities
        self._known_ids: set[str] = set()
        self._known_projection_ids: set[tuple[str, float]] = set()
        self._known_hotspot_ids: set[str] = set()
        self._known_satellite_zone_ids: set[str] = set()
        self._known_aircraft_ids: set[str] = set()

    def async_update_entities(self) -> None:
        """Add trackers for newly discovered nearby fires."""
        new_entities = []
        for alert in self._coordinator.nearby_alerts:
            if alert.has_location and alert.id not in self._known_ids:
                self._known_ids.add(alert.id)
                new_entities.append(FireTrackerEntity(self._coordinator, alert.id))

            if alert.has_location and self._coordinator.projection_for_alert(alert) is not None:
                for step in _PROJECTION_STEPS:
                    projection_id = (alert.id, step)
                    if projection_id in self._known_projection_ids:
                        continue
                    self._known_projection_ids.add(projection_id)
                    new_entities.append(FireProjectionTrackerEntity(self._coordinator, alert.id, step))

            if self._coordinator.satellite_zone_for_alert(alert.id) is not None:
                if alert.id not in self._known_satellite_zone_ids:
                    self._known_satellite_zone_ids.add(alert.id)
                    new_entities.append(FireSatelliteZoneTrackerEntity(self._coordinator, alert.id))

            for hotspot in self._coordinator.fire_hotspots.get(alert.id, []):
                if hotspot.hotspot_id in self._known_hotspot_ids:
                    continue
                self._known_hotspot_ids.add(hotspot.hotspot_id)
                new_entities.append(FireHotspotTrackerEntity(self._coordinator, hotspot.hotspot_id))

        for aircraft in self._coordinator.aircraft_positions.values():
            if aircraft.aircraft_id in self._known_aircraft_ids:
                continue
            self._known_aircraft_ids.add(aircraft.aircraft_id)
            new_entities.append(AircraftTrackerEntity(self._coordinator, aircraft.aircraft_id))
        if new_entities:
            self._async_add_entities(new_entities)


class FireTrackerEntity(FeuxDeForetEntity, TrackerEntity):
    """Represent one fire as a GPS tracker for Home Assistant maps."""

    _attr_icon = "mdi:fire"
    _attr_source_type = SourceType.GPS

    def __init__(self, coordinator: FeuxDeForetDataCoordinator, alert_id: str) -> None:
        """Initialize tracker."""
        super().__init__(coordinator)
        self._alert_id = alert_id
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_fire_{alert_id}"
        self._attr_suggested_object_id = f"pyroveille_fire_{slugify(alert_id)}"

    @property
    def _alert(self):
        return next((alert for alert in self.coordinator.nearby_alerts if alert.id == self._alert_id), None)

    @property
    def name(self) -> str:
        """Return tracker name."""
        alert = self._alert
        return alert.title if alert else f"Incendie {self._alert_id}"

    @property
    def latitude(self) -> float | None:
        """Return latitude."""
        alert = self._alert
        return alert.latitude if alert else None

    @property
    def longitude(self) -> float | None:
        """Return longitude."""
        alert = self._alert
        return alert.longitude if alert else None

    @property
    def location_accuracy(self) -> int:
        """Return accuracy in meters."""
        return 1000

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        """Return fire details."""
        alert = self._alert
        if not alert:
            return {"id": self._alert_id, "active": False, "fire_status": "unknown"}
        return {
            **alert.as_dict(),
            "fire_status": "active" if alert.active else "inactive",
            "marker_color": _ACTIVE_FIRE_COLOR if alert.active else _INACTIVE_FIRE_COLOR,
            "satellite_zone": self.coordinator.satellite_zone_for_alert(alert.id),
        }

    @property
    def entity_picture(self) -> str | None:
        """Return a colored fire marker for map cards."""
        alert = self._alert
        if alert is None:
            return None
        color = _ACTIVE_FIRE_COLOR if alert.active else _INACTIVE_FIRE_COLOR
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<circle cx="32" cy="32" r="30" fill="{color}"/>
<path fill="#ffffff" d="M34.8 6.6c-6.5 5.8-9 12.1-7.4 18.8.8 3.1-.6 6.1-3.6 7.7-2.4 1.3-5.2.8-7.1-1.2-4.1 5-6.1 10.1-6.1 15.1 0 8.2 6.4 14.2 21.4 14.2s21.4-6 21.4-14.2c0-7.4-5.1-13.8-10.8-19.6.2 3.8-1.4 6.8-4.6 8.6-1.7.9-3.9-.4-3.7-2.4.8-8.3-7-12.2.5-27z"/>
<path fill="{color}" d="M32 29l8 18h-5v10h-6V47h-5l8-18z"/>
</svg>"""
        return f"data:image/svg+xml;utf8,{quote(svg)}"


class FireProjectionTrackerEntity(FeuxDeForetEntity, TrackerEntity):
    """Represent one projected fire progression point as a GPS tracker."""

    _attr_icon = "mdi:clock-outline"
    _attr_source_type = SourceType.GPS

    def __init__(self, coordinator: FeuxDeForetDataCoordinator, alert_id: str, step: float) -> None:
        """Initialize projection tracker."""
        super().__init__(coordinator)
        self._alert_id = alert_id
        self._step = step
        step_label = int(step * 100)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_fire_{alert_id}_projection_{step_label}"
        self._attr_suggested_object_id = f"pyroveille_fire_{slugify(alert_id)}_projection_{step_label}"

    @property
    def _alert(self) -> FireAlert | None:
        return next((alert for alert in self.coordinator.nearby_alerts if alert.id == self._alert_id), None)

    @property
    def _projection(self) -> FireProjection | None:
        alert = self._alert
        if alert is None:
            return None
        return self.coordinator.projection_for_alert(alert)

    @property
    def available(self) -> bool:
        """Return whether the projection point can be displayed."""
        alert = self._alert
        projection = self._projection
        return bool(alert and alert.has_location and projection and projection.horizon_hours > 0)

    @property
    def name(self) -> str:
        """Return projection tracker name."""
        alert = self._alert
        step_label = int(self._step * 100)
        title = alert.title if alert else f"Incendie {self._alert_id}"
        return f"{title} projection {step_label}%"

    @property
    def latitude(self) -> float | None:
        """Return projected latitude."""
        point = self._projected_point()
        return point[0] if point else None

    @property
    def longitude(self) -> float | None:
        """Return projected longitude."""
        point = self._projected_point()
        return point[1] if point else None

    @property
    def location_accuracy(self) -> int:
        """Return projection accuracy in meters."""
        projection = self._projection
        if projection is None:
            return 1000
        return max(1000, int(projection.uncertainty_km * 1000))

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        """Return projection details."""
        projection = self._projection
        if projection is None:
            return {"id": self._alert_id, "projection": False}
        elapsed_hours = projection.horizon_hours * self._step
        projected_distance = projection.speed_kmh * elapsed_hours
        label = _format_projection_label(elapsed_hours)
        weather = self.coordinator.local_weather.get(self._alert_id)
        return {
            **projection.as_dict(),
            "id": self._alert_id,
            "projection": True,
            "projection_label": label,
            "projection_step": self._step,
            "projection_elapsed_hours": round(elapsed_hours, 2),
            "projection_distance_km": round(projected_distance, 2),
            "local_weather": weather.as_dict() if weather else None,
            "marker_color": _PROJECTION_COLOR,
        }

    @property
    def entity_picture(self) -> str | None:
        """Return a projection marker for map cards."""
        if not self.available:
            return None
        projection = self._projection
        if projection is None:
            return None
        label = _format_projection_label(projection.horizon_hours * self._step)
        font_size = 19 if len(label) <= 4 else 15
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<circle cx="32" cy="32" r="30" fill="{_PROJECTION_COLOR}"/>
<text x="32" y="37" text-anchor="middle" font-family="Arial, sans-serif" font-size="{font_size}" font-weight="700" fill="#ffffff">{label}</text>
</svg>"""
        return f"data:image/svg+xml;utf8,{quote(svg)}"

    def _projected_point(self) -> tuple[float, float] | None:
        """Return projected coordinates for this step."""
        alert = self._alert
        projection = self._projection
        if not alert or not alert.has_location or projection is None:
            return None
        distance = projection.distance_km * self._step
        return destination_point(alert.latitude, alert.longitude, projection.bearing, distance)


class FireSatelliteZoneTrackerEntity(FeuxDeForetEntity, TrackerEntity):
    """Represent one estimated NASA FIRMS satellite zone as a GPS tracker."""

    _attr_icon = "mdi:circle-opacity"
    _attr_source_type = SourceType.GPS

    def __init__(self, coordinator: FeuxDeForetDataCoordinator, alert_id: str) -> None:
        """Initialize satellite zone tracker."""
        super().__init__(coordinator)
        self._alert_id = alert_id
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_fire_{alert_id}_satellite_zone"
        self._attr_suggested_object_id = f"pyroveille_fire_{slugify(alert_id)}_satellite_zone"

    @property
    def _alert(self) -> FireAlert | None:
        return next((alert for alert in self.coordinator.nearby_alerts if alert.id == self._alert_id), None)

    @property
    def _satellite_zone(self) -> dict[str, object] | None:
        return self.coordinator.satellite_zone_for_alert(self._alert_id)

    @property
    def available(self) -> bool:
        """Return whether the satellite zone can be displayed."""
        return self._satellite_zone is not None

    @property
    def name(self) -> str:
        """Return satellite zone tracker name."""
        alert = self._alert
        title = alert.title if alert else f"Incendie {self._alert_id}"
        return f"{title} zone satellite estimee"

    @property
    def latitude(self) -> float | None:
        """Return satellite zone center latitude."""
        zone = self._satellite_zone
        return float(zone["center_latitude"]) if zone else None

    @property
    def longitude(self) -> float | None:
        """Return satellite zone center longitude."""
        zone = self._satellite_zone
        return float(zone["center_longitude"]) if zone else None

    @property
    def location_accuracy(self) -> int:
        """Return estimated zone radius in meters."""
        zone = self._satellite_zone
        if zone is None:
            return 1000
        return max(500, int(float(zone["estimated_radius_km"]) * 1000))

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        """Return satellite zone details."""
        zone = self._satellite_zone
        if zone is None:
            return {"id": self._alert_id, "satellite_zone": False}
        return {
            **zone,
            "id": self._alert_id,
            "satellite_zone": True,
            "estimated_radius_m": self.location_accuracy,
            "marker_color": _HOTSPOT_COLOR,
            "warning": "Zone estimee depuis les hotspots satellite FIRMS, pas un contour officiel.",
        }

    @property
    def entity_picture(self) -> str | None:
        """Return a translucent satellite zone marker for map cards."""
        if not self.available:
            return None
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<circle cx="32" cy="32" r="28" fill="{_HOTSPOT_COLOR}" opacity="0.28"/>
<circle cx="32" cy="32" r="28" fill="none" stroke="{_HOTSPOT_COLOR}" stroke-width="4" opacity="0.85"/>
<circle cx="32" cy="32" r="7" fill="{_HOTSPOT_COLOR}" opacity="0.95"/>
</svg>"""
        return f"data:image/svg+xml;utf8,{quote(svg)}"


class FireHotspotTrackerEntity(FeuxDeForetEntity, TrackerEntity):
    """Represent one NASA FIRMS hotspot as a GPS tracker."""

    _attr_icon = "mdi:fire-alert"
    _attr_source_type = SourceType.GPS

    def __init__(self, coordinator: FeuxDeForetDataCoordinator, hotspot_id: str) -> None:
        """Initialize hotspot tracker."""
        super().__init__(coordinator)
        self._hotspot_id = hotspot_id
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_hotspot_{hotspot_id}"
        self._attr_suggested_object_id = f"pyroveille_hotspot_{slugify(hotspot_id)}"

    @property
    def _hotspot(self) -> FireHotspot | None:
        for hotspots in self.coordinator.fire_hotspots.values():
            if hotspot := next((item for item in hotspots if item.hotspot_id == self._hotspot_id), None):
                return hotspot
        return None

    @property
    def available(self) -> bool:
        """Return whether the hotspot is still present."""
        return self._hotspot is not None

    @property
    def name(self) -> str:
        """Return hotspot tracker name."""
        hotspot = self._hotspot
        if hotspot is None:
            return f"Hotspot satellite {self._hotspot_id}"
        return f"Hotspot satellite {hotspot.fire_id}"

    @property
    def latitude(self) -> float | None:
        """Return hotspot latitude."""
        hotspot = self._hotspot
        return hotspot.latitude if hotspot else None

    @property
    def longitude(self) -> float | None:
        """Return hotspot longitude."""
        hotspot = self._hotspot
        return hotspot.longitude if hotspot else None

    @property
    def location_accuracy(self) -> int:
        """Return hotspot accuracy in meters."""
        hotspot = self._hotspot
        if hotspot and hotspot.scan:
            return max(375, int(hotspot.scan * 1000))
        return 1000

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        """Return hotspot details."""
        hotspot = self._hotspot
        if hotspot is None:
            return {"id": self._hotspot_id, "satellite_hotspot": False}
        return {
            **hotspot.as_dict(),
            "satellite_hotspot": True,
            "marker_color": _HOTSPOT_COLOR,
        }

    @property
    def entity_picture(self) -> str | None:
        """Return a satellite hotspot marker for map cards."""
        if not self.available:
            return None
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<circle cx="32" cy="32" r="22" fill="{_HOTSPOT_COLOR}" opacity="0.9"/>
<circle cx="32" cy="32" r="8" fill="#fff3e0"/>
<circle cx="32" cy="32" r="30" fill="none" stroke="{_HOTSPOT_COLOR}" stroke-width="4" opacity="0.55"/>
</svg>"""
        return f"data:image/svg+xml;utf8,{quote(svg)}"


class AircraftTrackerEntity(FeuxDeForetEntity, TrackerEntity):
    """Represent one live firefighting aircraft as a GPS tracker."""

    _attr_source_type = SourceType.GPS

    def __init__(self, coordinator: FeuxDeForetDataCoordinator, aircraft_id: str) -> None:
        """Initialize aircraft tracker."""
        super().__init__(coordinator)
        self._aircraft_id = aircraft_id
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_aircraft_{aircraft_id}"
        self._attr_suggested_object_id = f"pyroveille_aircraft_{slugify(aircraft_id)}"

    @property
    def _aircraft(self) -> AircraftPosition | None:
        return self.coordinator.aircraft_positions.get(self._aircraft_id)

    @property
    def available(self) -> bool:
        """Return whether the aircraft is still present in the live feed."""
        return self._aircraft is not None

    @property
    def name(self) -> str:
        """Return aircraft tracker name."""
        aircraft = self._aircraft
        if aircraft is None:
            return f"Aeronef {self._aircraft_id}"
        label = aircraft.callsign or aircraft.registration or aircraft.aircraft_id
        return f"{label} {aircraft.category_label}"

    @property
    def icon(self) -> str:
        """Return aircraft icon."""
        aircraft = self._aircraft
        if aircraft and aircraft.category == "heli":
            return "mdi:helicopter"
        return "mdi:airplane"

    @property
    def latitude(self) -> float | None:
        """Return aircraft latitude."""
        aircraft = self._aircraft
        return aircraft.latitude if aircraft else None

    @property
    def longitude(self) -> float | None:
        """Return aircraft longitude."""
        aircraft = self._aircraft
        return aircraft.longitude if aircraft else None

    @property
    def location_accuracy(self) -> int:
        """Return aircraft position accuracy in meters."""
        return 250

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        """Return aircraft details."""
        aircraft = self._aircraft
        if aircraft is None:
            return {"id": self._aircraft_id, "aircraft": False}
        color = _HELICOPTER_COLOR if aircraft.category == "heli" else _AIRCRAFT_COLOR
        return {
            **aircraft.as_dict(),
            "id": self._aircraft_id,
            "aircraft": True,
            "aircraft_type": aircraft.category,
            "marker_color": color,
        }

    @property
    def entity_picture(self) -> str | None:
        """Return an aircraft marker for map cards."""
        aircraft = self._aircraft
        if aircraft is None:
            return None
        color = _HELICOPTER_COLOR if aircraft.category == "heli" else _AIRCRAFT_COLOR
        heading = aircraft.heading or 0
        glyph = "H" if aircraft.category == "heli" else "A"
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<circle cx="32" cy="32" r="30" fill="{color}"/>
<g transform="rotate({heading} 32 32)">
<path fill="#ffffff" d="M32 8l9 31h-7l-2 9-2-9h-7L32 8z"/>
<path fill="#ffffff" opacity="0.92" d="M13 36l19-7 19 7v6l-19-4-19 4z"/>
</g>
<text x="32" y="58" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" font-weight="700" fill="#ffffff">{glyph}</text>
</svg>"""
        return f"data:image/svg+xml;utf8,{quote(svg)}"
