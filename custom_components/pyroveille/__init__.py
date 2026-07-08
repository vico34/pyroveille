"""PyroVeille integration."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .coordinator import FeuxDeForetDataCoordinator

STATIC_URL = "/pyroveille_static"
STATIC_PATH = Path(__file__).parent / "www"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PyroVeille from a config entry."""
    await _async_register_static_path(hass)
    coordinator = FeuxDeForetDataCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(coordinator.async_start_aircraft_tracking())
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


async def _async_register_static_path(hass: HomeAssistant) -> None:
    """Expose PyroVeille frontend assets."""
    registered = hass.data.setdefault(DOMAIN, {}).setdefault("_static_registered", False)
    if registered:
        return
    await hass.http.async_register_static_paths(
        [StaticPathConfig(STATIC_URL, str(STATIC_PATH), False)]
    )
    hass.data[DOMAIN]["_static_registered"] = True
