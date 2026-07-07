"""Sensors for PyroVeille."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfLength
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import slugify

from .const import DOMAIN
from .coordinator import FeuxDeForetDataCoordinator
from .entity import FeuxDeForetEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors."""
    coordinator: FeuxDeForetDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            NearbyFireCountSensor(coordinator),
            NearestFireDistanceSensor(coordinator),
            LastSuccessfulUpdateSensor(coordinator),
        ]
    )


class NearbyFireCountSensor(FeuxDeForetEntity, SensorEntity):
    """Count nearby fires."""

    _attr_name = "Incendies proches"
    _attr_icon = "mdi:fire-alert"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: FeuxDeForetDataCoordinator) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_nearby_fire_count"

    @property
    def native_value(self) -> int:
        """Return fire count."""
        return len(self.coordinator.nearby_alerts)


class NearestFireDistanceSensor(FeuxDeForetEntity, SensorEntity):
    """Distance to nearest nearby fire."""

    _attr_name = "Distance incendie le plus proche"
    _attr_icon = "mdi:map-marker-distance"
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: FeuxDeForetDataCoordinator) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_nearest_fire_distance"

    @property
    def native_value(self) -> float | None:
        """Return nearest distance."""
        alerts = self.coordinator.nearby_alerts
        if not alerts:
            return None
        return round(alerts[0].distance_km, 1) if alerts[0].distance_km is not None else None

    @property
    def extra_state_attributes(self) -> dict[str, object | None]:
        """Return nearest fire details."""
        alerts = self.coordinator.nearby_alerts
        return alerts[0].as_dict() if alerts else {}


class LastSuccessfulUpdateSensor(FeuxDeForetEntity, SensorEntity):
    """Expose last successful data update timestamp."""

    _attr_name = "Derniere mise a jour PyroVeille"
    _attr_icon = "mdi:update"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: FeuxDeForetDataCoordinator) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_last_successful_update"

    @property
    def native_value(self) -> datetime | None:
        """Return last successful update timestamp."""
        return self.coordinator.last_successful_update

    @property
    def extra_state_attributes(self) -> dict[str, object | None]:
        """Return update diagnostics."""
        return {
            "last_error": self.coordinator.last_error,
            "tracked_entities": [
                f"device_tracker.pyroveille_fire_{slugify(alert.id)}" for alert in self.coordinator.nearby_alerts
            ],
            "projection_entities": [
                f"device_tracker.pyroveille_fire_{slugify(alert.id)}_projection_{step}"
                for alert in self.coordinator.nearby_alerts
                if alert.id in self.coordinator.projections
                for step in (25, 50, 75, 100)
            ],
        }
