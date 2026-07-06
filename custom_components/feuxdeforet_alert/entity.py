"""Base entities for Feux de Foret Alert."""

from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FeuxDeForetDataCoordinator


class FeuxDeForetEntity(CoordinatorEntity[FeuxDeForetDataCoordinator]):
    """Base coordinator entity."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: FeuxDeForetDataCoordinator) -> None:
        """Initialize entity."""
        super().__init__(coordinator)
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.config_entry.entry_id)},
            "name": "PyroVeille",
            "manufacturer": "feuxdeforet.fr",
            "entry_type": "service",
        }
