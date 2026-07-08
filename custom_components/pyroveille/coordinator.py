"""Data coordinator for PyroVeille."""

from __future__ import annotations

import logging
import asyncio
from datetime import datetime
from math import atan2, cos, degrees, radians, sin

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import FeuxDeForetApiError, FeuxDeForetClient
from .const import (
    CONF_API_BASE_URL,
    CONF_CENTER_LATITUDE,
    CONF_CENTER_LONGITUDE,
    CONF_CREATE_PERSISTENT_NOTIFICATIONS,
    CONF_CREATE_TELEGRAM_NOTIFICATIONS,
    CONF_DEPARTMENTS,
    CONF_ENABLE_AIRCRAFT_TRACKING,
    CONF_ENABLE_PROJECTIONS,
    CONF_ENABLE_SATELLITE_ZONES,
    CONF_FIRMS_MAP_KEY,
    CONF_FIRMS_SEARCH_RADIUS_KM,
    CONF_FIRMS_SOURCE,
    CONF_GEOCODE_MISSING_COORDINATES,
    CONF_INCLUDE_LINK_IN_NOTIFICATIONS,
    CONF_NOTIFICATION_MAX_DISTANCE_KM,
    CONF_ONLY_ACTIVE,
    CONF_RADIUS_KM,
    CONF_TELEGRAM_NOTIFY_SERVICE,
    DEFAULT_API_BASE_URL,
    DEFAULT_AUTO_PROJECTION_HORIZON_HOURS,
    DEFAULT_AUTO_PROJECTION_UNCERTAINTY_KM,
    DEFAULT_AUTO_PROJECTION_WIND_FACTOR,
    DEFAULT_CREATE_PERSISTENT_NOTIFICATIONS,
    DEFAULT_CREATE_TELEGRAM_NOTIFICATIONS,
    DEFAULT_ENABLE_AIRCRAFT_TRACKING,
    DEFAULT_ENABLE_PROJECTIONS,
    DEFAULT_ENABLE_SATELLITE_ZONES,
    DEFAULT_FIRMS_DAY_RANGE,
    DEFAULT_FIRMS_SEARCH_RADIUS_KM,
    DEFAULT_FIRMS_SOURCE,
    DEFAULT_GEOCODE_MISSING_COORDINATES,
    DEFAULT_INCLUDE_LINK_IN_NOTIFICATIONS,
    DEFAULT_MAX_ITEMS,
    DEFAULT_NOTIFICATION_MAX_DISTANCE_KM,
    DEFAULT_ONLY_ACTIVE,
    DEFAULT_RADIUS_KM,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TELEGRAM_NOTIFY_SERVICE,
    DOMAIN,
    EVENT_NEARBY_FIRE,
)
from .models import AircraftPosition, FireAlert, FireHotspot, FireProjection, LocalWeather
from .util import destination_point, distance_km, parse_departments

_LOGGER = logging.getLogger(__name__)


class FeuxDeForetDataCoordinator(DataUpdateCoordinator[list[FireAlert]]):
    """Coordinate feuxdeforet.fr polling and local filtering."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.config_entry = entry
        data = entry.data
        options = entry.options
        self.center_latitude = float(options.get(CONF_CENTER_LATITUDE, data.get(CONF_CENTER_LATITUDE)))
        self.center_longitude = float(options.get(CONF_CENTER_LONGITUDE, data.get(CONF_CENTER_LONGITUDE)))
        self.radius_km = float(options.get(CONF_RADIUS_KM, data.get(CONF_RADIUS_KM, DEFAULT_RADIUS_KM)))
        self.departments = parse_departments(options.get(CONF_DEPARTMENTS, data.get(CONF_DEPARTMENTS)))
        self.only_active = bool(options.get(CONF_ONLY_ACTIVE, data.get(CONF_ONLY_ACTIVE, DEFAULT_ONLY_ACTIVE)))
        self.create_notifications = bool(
            options.get(
                CONF_CREATE_PERSISTENT_NOTIFICATIONS,
                data.get(CONF_CREATE_PERSISTENT_NOTIFICATIONS, DEFAULT_CREATE_PERSISTENT_NOTIFICATIONS),
            )
        )
        self.notification_max_distance_km = float(
            options.get(
                CONF_NOTIFICATION_MAX_DISTANCE_KM,
                data.get(CONF_NOTIFICATION_MAX_DISTANCE_KM, DEFAULT_NOTIFICATION_MAX_DISTANCE_KM),
            )
        )
        self.include_link_in_notifications = bool(
            options.get(
                CONF_INCLUDE_LINK_IN_NOTIFICATIONS,
                data.get(CONF_INCLUDE_LINK_IN_NOTIFICATIONS, DEFAULT_INCLUDE_LINK_IN_NOTIFICATIONS),
            )
        )
        self.create_telegram_notifications = bool(
            options.get(
                CONF_CREATE_TELEGRAM_NOTIFICATIONS,
                data.get(CONF_CREATE_TELEGRAM_NOTIFICATIONS, DEFAULT_CREATE_TELEGRAM_NOTIFICATIONS),
            )
        )
        self.telegram_notify_service = str(
            options.get(
                CONF_TELEGRAM_NOTIFY_SERVICE,
                data.get(CONF_TELEGRAM_NOTIFY_SERVICE, DEFAULT_TELEGRAM_NOTIFY_SERVICE),
            )
        ).strip()
        self.last_telegram_notification_error: str | None = None
        self.enable_projections = bool(
            options.get(CONF_ENABLE_PROJECTIONS, data.get(CONF_ENABLE_PROJECTIONS, DEFAULT_ENABLE_PROJECTIONS))
        )
        self.enable_satellite_zones = bool(
            options.get(
                CONF_ENABLE_SATELLITE_ZONES,
                data.get(CONF_ENABLE_SATELLITE_ZONES, DEFAULT_ENABLE_SATELLITE_ZONES),
            )
        )
        self.enable_aircraft_tracking = bool(
            options.get(
                CONF_ENABLE_AIRCRAFT_TRACKING,
                data.get(CONF_ENABLE_AIRCRAFT_TRACKING, DEFAULT_ENABLE_AIRCRAFT_TRACKING),
            )
        )
        self.firms_map_key = str(options.get(CONF_FIRMS_MAP_KEY, data.get(CONF_FIRMS_MAP_KEY, ""))).strip()
        self.firms_source = str(
            options.get(CONF_FIRMS_SOURCE, data.get(CONF_FIRMS_SOURCE, DEFAULT_FIRMS_SOURCE))
        ).strip()
        self.firms_search_radius_km = float(
            options.get(
                CONF_FIRMS_SEARCH_RADIUS_KM,
                data.get(CONF_FIRMS_SEARCH_RADIUS_KM, DEFAULT_FIRMS_SEARCH_RADIUS_KM),
            )
        )
        self.auto_projection_horizon_hours = DEFAULT_AUTO_PROJECTION_HORIZON_HOURS
        self.auto_projection_uncertainty_km = DEFAULT_AUTO_PROJECTION_UNCERTAINTY_KM
        self.auto_projection_wind_factor = DEFAULT_AUTO_PROJECTION_WIND_FACTOR
        self._seen_nearby_ids: set[str] = set()
        self.last_successful_update: datetime | None = None
        self.last_error: str | None = None
        self.local_weather: dict[str, LocalWeather] = {}
        self.fire_hotspots: dict[str, list[FireHotspot]] = {}
        self.aircraft_positions: dict[str, AircraftPosition] = {}
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

    def projection_for_alert(self, alert: FireAlert) -> FireProjection | None:
        """Return weather-based automatic projection for an alert."""
        if not self.enable_projections:
            return None
        weather = self.local_weather.get(alert.id)
        if weather is None or weather.downwind_bearing is None or weather.wind_speed_kmh is None:
            return None
        speed_kmh = weather.wind_speed_kmh * self.auto_projection_wind_factor
        if speed_kmh <= 0 or self.auto_projection_horizon_hours <= 0:
            return None
        return FireProjection(
            fire_id=alert.id,
            bearing=weather.downwind_bearing,
            speed_kmh=speed_kmh,
            horizon_hours=max(0.0, self.auto_projection_horizon_hours),
            uncertainty_km=max(0.0, self.auto_projection_uncertainty_km),
            mode="weather",
        )

    @property
    def active_projections(self) -> dict[str, FireProjection]:
        """Return projections currently applied to nearby alerts."""
        return {
            alert.id: projection
            for alert in self.nearby_alerts
            if (projection := self.projection_for_alert(alert)) is not None
        }

    async def _async_update_data(self) -> list[FireAlert]:
        """Fetch and filter recent fires."""
        try:
            alerts = await self.client.async_get_recent_fires(DEFAULT_MAX_ITEMS)
        except FeuxDeForetApiError as err:
            self.last_error = str(err)
            raise UpdateFailed(str(err)) from err

        nearby = [self._with_distance(alert) for alert in alerts]
        nearby = [alert for alert in nearby if self._is_in_scope(alert)]
        nearby.sort(key=lambda alert: alert.distance_km if alert.distance_km is not None else 999999)
        await asyncio.gather(
            self._async_update_local_weather(nearby),
            self._async_update_fire_hotspots(nearby),
            self._async_update_aircraft_positions(),
        )

        self.last_successful_update = dt_util.utcnow()
        self.last_error = None
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
            if not self._should_notify(alert):
                continue
            if self.create_notifications:
                persistent_notification.async_create(
                    self.hass,
                    self._notification_message(alert),
                    title="Alerte incendie a proximite",
                    notification_id=f"{DOMAIN}_{alert.id}",
                )
            if self.create_telegram_notifications:
                await self._async_send_telegram_notification(alert)

    async def _async_send_telegram_notification(self, alert: FireAlert) -> None:
        """Send a Telegram notification through an existing Home Assistant notify service."""
        target = self.telegram_notify_service
        if not target:
            return
        message = self._notification_message(alert)
        legacy_service = target.removeprefix("notify.") if target.startswith("notify.") else target
        try:
            if self.hass.services.has_service("notify", legacy_service):
                await self.hass.services.async_call(
                    "notify",
                    legacy_service,
                    {
                        "title": "Alerte incendie a proximite",
                        "message": message,
                        "data": {"url": alert.url} if alert.url else {},
                    },
                    blocking=True,
                )
                self.last_telegram_notification_error = None
                return

            notify_entity = target if target.startswith("notify.") else f"notify.{target}"
            if self.hass.services.has_service("notify", "send_message") and self.hass.states.get(notify_entity):
                await self.hass.services.async_call(
                    "notify",
                    "send_message",
                    {
                        "entity_id": notify_entity,
                        "message": f"Alerte incendie a proximite\n\n{message}",
                    },
                    blocking=True,
                )
                self.last_telegram_notification_error = None
                return

            self.last_telegram_notification_error = (
                f"Notify target '{target}' is not available. Use a legacy service like 'telegram' "
                "or a notify entity like 'notify.telegram_bot_chat'."
            )
            _LOGGER.warning("Telegram notifications enabled but %s", self.last_telegram_notification_error)
        except Exception as err:  # noqa: BLE001
            self.last_telegram_notification_error = str(err)
            _LOGGER.warning("Telegram notification failed: %s", err)

    def _notification_message(self, alert: FireAlert) -> str:
        """Build persistent notification content."""
        distance = f"{alert.distance_km:.1f} km" if alert.distance_km is not None else "distance inconnue"
        link = f"\n\n{alert.url}" if self.include_link_in_notifications and alert.url else ""
        return f"{alert.title}\nLocalisation: {alert.location_name}\nDistance: {distance}{link}"

    def _should_notify(self, alert: FireAlert) -> bool:
        """Return whether an alert should trigger notifications."""
        if self.notification_max_distance_km <= 0:
            return True
        if alert.distance_km is None:
            return False
        return alert.distance_km <= self.notification_max_distance_km

    async def _async_update_local_weather(self, alerts: list[FireAlert]) -> None:
        """Fetch local weather for nearby alerts with coordinates."""
        if not self.enable_projections:
            self.local_weather = {}
            return
        located_alerts = [alert for alert in alerts if alert.has_location]
        weather_results = await asyncio.gather(
            *[
                self.client.async_get_local_weather(alert.latitude, alert.longitude)
                for alert in located_alerts
            ]
        )
        weather_by_id = {
            alert.id: weather
            for alert, weather in zip(located_alerts, weather_results, strict=False)
            if weather is not None
        }
        self.local_weather = weather_by_id

    async def _async_update_fire_hotspots(self, alerts: list[FireAlert]) -> None:
        """Fetch satellite hotspots around nearby alerts."""
        if not self.enable_satellite_zones or not self.firms_map_key:
            self.fire_hotspots = {}
            return
        located_alerts = [alert for alert in alerts if alert.has_location]
        hotspot_results = await asyncio.gather(
            *[
                self.client.async_get_fire_hotspots(
                    alert,
                    map_key=self.firms_map_key,
                    source=self.firms_source,
                    radius_km=self.firms_search_radius_km,
                    day_range=DEFAULT_FIRMS_DAY_RANGE,
                )
                for alert in located_alerts
            ]
        )
        self.fire_hotspots = {
            alert.id: hotspots
            for alert, hotspots in zip(located_alerts, hotspot_results, strict=False)
            if hotspots
        }

    async def _async_update_aircraft_positions(self) -> None:
        """Fetch live aircraft positions."""
        if not self.enable_aircraft_tracking:
            self.aircraft_positions = {}
            return
        try:
            aircraft = await self.client.async_get_aircraft_positions()
        except FeuxDeForetApiError as err:
            _LOGGER.debug("Could not fetch aircraft positions: %s", err)
            self.aircraft_positions = {}
            return
        self.aircraft_positions = {item.aircraft_id: item for item in aircraft}

    def satellite_zone_for_alert(self, alert_id: str) -> dict[str, object] | None:
        """Return estimated satellite zone details for an alert."""
        hotspots = self.fire_hotspots.get(alert_id) or []
        if not hotspots:
            return None
        latitudes = [hotspot.latitude for hotspot in hotspots]
        longitudes = [hotspot.longitude for hotspot in hotspots]
        center_latitude = sum(latitudes) / len(latitudes)
        center_longitude = sum(longitudes) / len(longitudes)
        estimated_radius = max(
            distance_km(center_latitude, center_longitude, hotspot.latitude, hotspot.longitude)
            for hotspot in hotspots
        )
        polygon = _satellite_zone_polygon(center_latitude, center_longitude, hotspots)
        return {
            "source": "nasa-firms",
            "mode": "satellite_hotspots",
            "hotspot_count": len(hotspots),
            "center_latitude": round(center_latitude, 6),
            "center_longitude": round(center_longitude, 6),
            "estimated_radius_km": round(max(estimated_radius, 0.5), 2),
            "area_km2": _polygon_area_km2(polygon),
            "geojson": {
                "type": "Feature",
                "properties": {
                    "source": "nasa-firms",
                    "mode": "estimated_satellite_zone",
                    "fire_id": alert_id,
                    "hotspot_count": len(hotspots),
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [round(longitude, 6), round(latitude, 6)]
                        for latitude, longitude in polygon
                    ]],
                },
            },
            "bbox": {
                "south": round(min(latitudes), 6),
                "west": round(min(longitudes), 6),
                "north": round(max(latitudes), 6),
                "east": round(max(longitudes), 6),
            },
        }


def _satellite_zone_polygon(
    center_latitude: float,
    center_longitude: float,
    hotspots: list[FireHotspot],
) -> list[tuple[float, float]]:
    """Build a lightweight irregular polygon around satellite hotspots."""
    if len(hotspots) == 1:
        radius_km = _hotspot_radius_km(hotspots[0])
        return [
            destination_point(center_latitude, center_longitude, bearing, radius_km)
            for bearing in range(0, 361, 30)
        ]

    points = sorted(
        hotspots,
        key=lambda hotspot: _bearing_degrees(
            center_latitude,
            center_longitude,
            hotspot.latitude,
            hotspot.longitude,
        ),
    )
    polygon = []
    for hotspot in points:
        bearing = _bearing_degrees(center_latitude, center_longitude, hotspot.latitude, hotspot.longitude)
        distance = distance_km(center_latitude, center_longitude, hotspot.latitude, hotspot.longitude)
        radius = _hotspot_radius_km(hotspot)
        polygon.append(destination_point(center_latitude, center_longitude, bearing, distance + radius))

    if len(polygon) == 2:
        return _capsule_polygon(center_latitude, center_longitude, points)

    polygon.append(polygon[0])
    return polygon


def _capsule_polygon(
    center_latitude: float,
    center_longitude: float,
    hotspots: list[FireHotspot],
) -> list[tuple[float, float]]:
    """Build a capsule-shaped polygon when only two hotspots are available."""
    first, second = hotspots
    first_bearing = _bearing_degrees(first.latitude, first.longitude, second.latitude, second.longitude)
    second_bearing = (first_bearing + 180) % 360
    radius = max(_hotspot_radius_km(first), _hotspot_radius_km(second))
    points = [
        destination_point(first.latitude, first.longitude, (first_bearing - 90) % 360, radius),
        destination_point(second.latitude, second.longitude, (first_bearing - 90) % 360, radius),
        destination_point(second.latitude, second.longitude, (second_bearing - 90) % 360, radius),
        destination_point(first.latitude, first.longitude, (second_bearing - 90) % 360, radius),
    ]
    points.sort(
        key=lambda point: _bearing_degrees(center_latitude, center_longitude, point[0], point[1])
    )
    points.append(points[0])
    return points


def _hotspot_radius_km(hotspot: FireHotspot) -> float:
    """Return an estimated footprint radius for a hotspot."""
    footprint = max(hotspot.scan or 0.0, hotspot.track or 0.0, 0.5)
    return max(0.5, footprint / 2)


def _bearing_degrees(latitude: float, longitude: float, to_latitude: float, to_longitude: float) -> float:
    """Return initial bearing in degrees."""
    lat1 = radians(latitude)
    lat2 = radians(to_latitude)
    delta_lon = radians(to_longitude - longitude)
    y = sin(delta_lon) * cos(lat2)
    x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(delta_lon)
    return (degrees(atan2(y, x)) + 360) % 360


def _polygon_area_km2(polygon: list[tuple[float, float]]) -> float:
    """Return approximate polygon area using a local equirectangular projection."""
    if len(polygon) < 4:
        return 0.0
    origin_latitude = sum(point[0] for point in polygon[:-1]) / (len(polygon) - 1)
    projected = [
        (
            point[1] * 111.320 * cos(radians(origin_latitude)),
            point[0] * 110.574,
        )
        for point in polygon
    ]
    area = 0.0
    for index, point in enumerate(projected[:-1]):
        next_point = projected[index + 1]
        area += point[0] * next_point[1] - next_point[0] * point[1]
    return round(abs(area) / 2, 2)
