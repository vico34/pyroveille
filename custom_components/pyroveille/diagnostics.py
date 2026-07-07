"""Diagnostics support for PyroVeille."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import FeuxDeForetDataCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, object]:
    """Return diagnostics for a config entry."""
    coordinator: FeuxDeForetDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    return {
        "entry": {
            "data": dict(entry.data),
            "options": dict(entry.options),
        },
        "nearby_alert_count": len(coordinator.nearby_alerts),
        "nearby_alerts": [alert.as_dict() for alert in coordinator.nearby_alerts],
        "active_projections": {
            fire_id: projection.as_dict() for fire_id, projection in coordinator.active_projections.items()
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
