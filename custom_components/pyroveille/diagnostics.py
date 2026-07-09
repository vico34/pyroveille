"""Diagnostics support for PyroVeille."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_FIRMS_MAP_KEY, DOMAIN
from .coordinator import FeuxDeForetDataCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, object]:
    """Return diagnostics for a config entry."""
    coordinator: FeuxDeForetDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    data = _redact_sensitive(dict(entry.data))
    options = _redact_sensitive(dict(entry.options))
    return {
        "entry": {
            "data": data,
            "options": options,
        },
        "nearby_alert_count": len(coordinator.nearby_alerts),
        "nearby_alerts": [alert.as_dict() for alert in coordinator.nearby_alerts],
        "active_projections": {
            fire_id: projection.as_dict() for fire_id, projection in coordinator.active_projections.items()
        },
        "satellite_zones": {
            fire_id: coordinator.satellite_zone_for_alert(fire_id)
            for fire_id in coordinator.fire_hotspots
        },
        "satellite_hotspots": {
            fire_id: [hotspot.as_dict() for hotspot in hotspots]
            for fire_id, hotspots in coordinator.fire_hotspots.items()
        },
        "local_weather": {
            fire_id: weather.as_dict() for fire_id, weather in coordinator.local_weather.items()
        },
        "automatic_projections": {
            "enabled": coordinator.enable_projections,
            "horizon_hours": coordinator.auto_projection_horizon_hours,
            "uncertainty_km": coordinator.auto_projection_uncertainty_km,
            "wind_factor": coordinator.auto_projection_wind_factor,
        },
        "telegram_notifications": {
            "enabled": coordinator.create_telegram_notifications,
            "target": coordinator.telegram_notify_service,
            "last_error": coordinator.last_telegram_notification_error,
        },
        "firms": {
            "enabled": coordinator.enable_satellite_zones,
            "source": coordinator.firms_source,
            "search_radius_km": coordinator.firms_search_radius_km,
            "has_map_key": bool(coordinator.firms_map_key),
        },
        "aircraft_tracking": {
            "enabled": coordinator.enable_aircraft_tracking,
            "aircraft_count": len(coordinator.aircraft_positions),
            "adsb_aircraft_count": len(coordinator.adsb_aircraft_positions),
            "last_error": coordinator.last_aircraft_tracking_error,
            "adsb_last_error": coordinator.last_adsb_aircraft_error,
            "aircraft": {
                aircraft_id: aircraft.as_dict()
                for aircraft_id, aircraft in coordinator.aircraft_positions.items()
            },
        },
        "last_successful_update": coordinator.last_successful_update.isoformat()
        if coordinator.last_successful_update
        else None,
        "last_error": coordinator.last_error,
        "center": {
            "latitude": coordinator.center_latitude,
            "longitude": coordinator.center_longitude,
            "radius_km": coordinator.radius_km,
        },
    }


def _redact_sensitive(data: dict[str, object]) -> dict[str, object]:
    """Redact secrets from diagnostics."""
    if data.get(CONF_FIRMS_MAP_KEY):
        data[CONF_FIRMS_MAP_KEY] = "**REDACTED**"
    return data
