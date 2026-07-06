"""Binary sensors for PyroVeille."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import FeuxDeForetDataCoordinator
from .entity import FeuxDeForetEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensors."""
    coordinator: FeuxDeForetDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([NearbyFireBinarySensor(coordinator)])


class NearbyFireBinarySensor(FeuxDeForetEntity, BinarySensorEntity):
    """Report whether at least one fire is in scope."""

    _attr_name = "Alerte incendie proche"
    _attr_device_class = BinarySensorDeviceClass.SAFETY

    def __init__(self, coordinator: FeuxDeForetDataCoordinator) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_nearby_fire"

    @property
    def is_on(self) -> bool:
        """Return true when at least one nearby fire exists."""
        return bool(self.coordinator.nearby_alerts)

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        """Return extra state attributes."""
        alerts = self.coordinator.nearby_alerts
        nearest = alerts[0] if alerts else None
        return {
            "count": len(alerts),
            "radius_km": self.coordinator.radius_km,
            "nearest": nearest.as_dict() if nearest else None,
            "alerts": [alert.as_dict() for alert in alerts],
        }
