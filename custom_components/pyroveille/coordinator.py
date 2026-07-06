"""Data coordinator for PyroVeille."""

from __future__ import annotations

import logging

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import FeuxDeForetApiError, FeuxDeForetClient
from .const import (
    CONF_API_BASE_URL,
    CONF_CENTER_LATITUDE,
    CONF_CENTER_LONGITUDE,
    CONF_CREATE_PERSISTENT_NOTIFICATIONS,
    CONF_DEPARTMENTS,
    CONF_GEOCODE_MISSING_COORDINATES,
    CONF_ONLY_ACTIVE,
    CONF_RADIUS_KM,
    DEFAULT_API_BASE_URL,
    DEFAULT_CREATE_PERSISTENT_NOTIFICATIONS,
    DEFAULT_GEOCODE_MISSING_COORDINATES,
    DEFAULT_MAX_ITEMS,
    DEFAULT_ONLY_ACTIVE,
    DEFAULT_RADIUS_KM,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    EVENT_NEARBY_FIRE,
)
from .models import FireAlert
from .util import distance_km, parse_departments

_LOGGER = logging.getLogger(__name__)


class FeuxDeForetDataCoordinator(DataUpdateCoordinator[list[FireAlert]]):
    """Coordinate feuxdeforet.fr polling and local filtering."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.config_entry = entry
        data = entry.data
        options = entry.options
        self.center_latitude = float(data.get(CONF_CENTER_LATITUDE))
        self.center_longitude = float(data.get(CONF_CENTER_LONGITUDE))
        self.radius_km = float(options.get(CONF_RADIUS_KM, data.get(CONF_RADIUS_KM, DEFAULT_RADIUS_KM)))
        self.departments = parse_departments(options.get(CONF_DEPARTMENTS, data.get(CONF_DEPARTMENTS)))
        self.only_active = bool(options.get(CONF_ONLY_ACTIVE, data.get(CONF_ONLY_ACTIVE, DEFAULT_ONLY_ACTIVE)))
        self.create_notifications = bool(
            options.get(
                CONF_CREATE_PERSISTENT_NOTIFICATIONS,
                data.get(CONF_CREATE_PERSISTENT_NOTIFICATIONS, DEFAULT_CREATE_PERSISTENT_NOTIFICATIONS),
            )
        )
        self._seen_nearby_ids: set[str] = set()
        self.client = FeuxDeForetClient(
            hass,
            options.get(CONF_API_BASE_URL, data.get(CONF_API_BASE_URL, DEFAULT_API_BASE_URL)),
            geocode_missing=bool(
                options.get(
                    CONF_GEOCODE_MISSING_COORDINATES,
                    data.get(CONF_GEOCODE_MISSING_COORDINATES, DEFAULT_GEOCODE_MISSING_COORDINATES),
                )
            ),
        )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )

    @property
    def nearby_alerts(self) -> list[FireAlert]:
        """Return latest nearby alerts."""
        return self.data or []

    async def _async_update_data(self) -> list[FireAlert]:
        """Fetch and filter recent fires."""
        try:
            alerts = await self.client.async_get_recent_fires(DEFAULT_MAX_ITEMS)
        except FeuxDeForetApiError as err:
            raise UpdateFailed(str(err)) from err

        nearby = [self._with_distance(alert) for alert in alerts]
        nearby = [alert for alert in nearby if self._is_in_scope(alert)]
        nearby.sort(key=lambda alert: alert.distance_km if alert.distance_km is not None else 999999)

        await self._async_emit_new_alerts(nearby)
        return nearby

    def _with_distance(self, alert: FireAlert) -> FireAlert:
        """Attach distance from configured center when possible."""
        if not alert.has_location:
            return alert
        return FireAlert(
            **{
                **alert.as_dict(),
                "date": alert.date,
                "distance_km": distance_km(
                    self.center_latitude,
                    self.center_longitude,
                    alert.latitude,
                    alert.longitude,
                ),
            }
        )

    def _is_in_scope(self, alert: FireAlert) -> bool:
        """Return whether an alert matches configured filters."""
        if self.only_active and not alert.active:
            return False
        if self.departments and (alert.department or "").upper().zfill(2) not in self.departments:
            return False
        if alert.distance_km is None:
            return False
        return alert.distance_km <= self.radius_km

    async def _async_emit_new_alerts(self, alerts: list[FireAlert]) -> None:
        """Fire HA events and optional persistent notifications for new nearby alerts."""
        for alert in alerts:
            if alert.id in self._seen_nearby_ids:
                continue
            self._seen_nearby_ids.add(alert.id)
            payload = alert.as_dict()
            self.hass.bus.async_fire(EVENT_NEARBY_FIRE, payload)
            if self.create_notifications:
                persistent_notification.async_create(
                    self.hass,
                    self._notification_message(alert),
                    title="Alerte incendie a proximite",
                    notification_id=f"{DOMAIN}_{alert.id}",
                )

    def _notification_message(self, alert: FireAlert) -> str:
        """Build persistent notification content."""
        distance = f"{alert.distance_km:.1f} km" if alert.distance_km is not None else "distance inconnue"
        link = f"\n\n{alert.url}" if alert.url else ""
        return f"{alert.title}\nLocalisation: {alert.location_name}\nDistance: {distance}{link}"
