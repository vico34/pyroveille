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

_ACTIVE_FIRE_COLOR = "#e53935"
_INACTIVE_FIRE_COLOR = "#757575"


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
