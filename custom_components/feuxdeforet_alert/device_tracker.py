"""Device tracker entities for map display."""

from __future__ import annotations

from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.components.device_tracker.const import SourceType
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

    def async_update_entities(self) -> None:
        """Add trackers for newly discovered nearby fires."""
        new_entities = []
        for alert in self._coordinator.nearby_alerts:
            if not alert.has_location or alert.id in self._known_ids:
                continue
            self._known_ids.add(alert.id)
            new_entities.append(FireTrackerEntity(self._coordinator, alert.id))
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
        return alert.as_dict() if alert else {"id": self._alert_id, "active": False}
