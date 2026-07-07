"""PyroVeille integration."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    PLATFORMS,
    SERVICE_CLEAR_ALL_PROJECTIONS,
    SERVICE_CLEAR_FIRE_PROJECTION,
    SERVICE_SET_FIRE_PROJECTION,
)
from .coordinator import FeuxDeForetDataCoordinator

_SERVICE_SET_PROJECTION_SCHEMA = vol.Schema(
    {
        vol.Required("fire_id"): cv.string,
        vol.Required("bearing"): vol.All(vol.Coerce(float), vol.Range(min=0, max=359)),
        vol.Required("speed_kmh"): vol.All(vol.Coerce(float), vol.Range(min=0)),
        vol.Required("horizon_hours"): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=72)),
        vol.Optional("uncertainty_km", default=0.0): vol.All(vol.Coerce(float), vol.Range(min=0)),
    }
)
_SERVICE_CLEAR_PROJECTION_SCHEMA = vol.Schema({vol.Required("fire_id"): cv.string})


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PyroVeille from a config entry."""
    coordinator = FeuxDeForetDataCoordinator(hass, entry)
    await coordinator.async_load_projections()
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    _async_register_services(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry after option updates."""
    await hass.config_entries.async_reload(entry.entry_id)


def _async_register_services(hass: HomeAssistant) -> None:
    """Register PyroVeille services once."""
    if hass.data[DOMAIN].get("services_registered"):
        return

    async def async_set_fire_projection(call: ServiceCall) -> None:
        """Set a fire projection on matching coordinators."""
        fire_id = call.data["fire_id"]
        for coordinator in _coordinators(hass):
            await coordinator.async_set_projection(
                fire_id,
                call.data["bearing"],
                call.data["speed_kmh"],
                call.data["horizon_hours"],
                call.data["uncertainty_km"],
            )

    async def async_clear_fire_projection(call: ServiceCall) -> None:
        """Clear one fire projection on matching coordinators."""
        fire_id = call.data["fire_id"]
        for coordinator in _coordinators(hass):
            await coordinator.async_clear_projection(fire_id)

    async def async_clear_all_projections(call: ServiceCall) -> None:
        """Clear all fire projections."""
        for coordinator in _coordinators(hass):
            await coordinator.async_clear_all_projections()

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_FIRE_PROJECTION,
        async_set_fire_projection,
        schema=_SERVICE_SET_PROJECTION_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CLEAR_FIRE_PROJECTION,
        async_clear_fire_projection,
        schema=_SERVICE_CLEAR_PROJECTION_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CLEAR_ALL_PROJECTIONS,
        async_clear_all_projections,
    )
    hass.data[DOMAIN]["services_registered"] = True


def _coordinators(hass: HomeAssistant) -> list[FeuxDeForetDataCoordinator]:
    """Return loaded PyroVeille coordinators."""
    return [
        coordinator
        for coordinator in hass.data.get(DOMAIN, {}).values()
        if isinstance(coordinator, FeuxDeForetDataCoordinator)
    ]
