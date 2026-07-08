"""Client for public feuxdeforet.fr data."""

from __future__ import annotations

import logging
import re
import csv
from datetime import datetime
from io import StringIO
from math import atan2, cos, degrees, radians, sin
from typing import Any
from urllib.parse import urljoin

from aiohttp import ClientError, ClientSession
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DEFAULT_FEUXDEFORET_BASE_URL, DEFAULT_MAX_ITEMS
from .models import AircraftPosition, FireAlert, FireHotspot, LocalWeather
from .util import distance_km

_LOGGER = logging.getLogger(__name__)

USER_AGENT = "HomeAssistant-PyroVeille/0.4.0-beta.9"
ADRESSE_GOUV_URL = "https://api-adresse.data.gouv.fr/search/"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
FIRMS_AREA_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
FEUXDEFORET_HOME_URL = "https://feuxdeforet.fr"
FEUXDEFORET_AIRCRAFT_URL = "https://feuxdeforet.fr/fdf/tracker/aircraft"


class FeuxDeForetApiError(Exception):
    """Raised when feuxdeforet.fr data cannot be fetched."""


class FeuxDeForetClient:
    """Small client for feuxdeforet.fr public routes."""

    def __init__(
        self,
        hass,
        api_base_url: str,
        *,
        geocode_missing: bool,
    ) -> None:
        """Initialize the client."""
        self._session: ClientSession = async_get_clientsession(hass)
        self._api_base_url = api_base_url.rstrip("/")
        self._geocode_missing = geocode_missing
        self._geocode_cache: dict[str, tuple[float, float] | None] = {}
        self._proxy_nonce: str | None = None

    async def async_get_recent_fires(self, max_items: int = DEFAULT_MAX_ITEMS) -> list[FireAlert]:
        """Fetch recent fire reports."""
        per = max(1, min(max_items, 100))
        payload = await self._request_json(f"/signalements/recent?per={per}")
        items = payload.get("signalements") or payload.get("feux") or []
        alerts = [self._normalize_fire(item) for item in items if isinstance(item, dict)]

        if self._geocode_missing:
            alerts = [await self._async_geocode_alert(alert) for alert in alerts]

        return alerts

    async def _request_json(self, path: str) -> dict[str, Any]:
        """Request JSON from the configured public API base."""
        url = f"{self._api_base_url}{path}"
        headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
        try:
            async with self._session.get(url, headers=headers, timeout=20) as response:
                if response.status >= 400:
                    raise FeuxDeForetApiError(f"{url} returned HTTP {response.status}")
                data = await response.json(content_type=None)
        except (ClientError, TimeoutError) as err:
            raise FeuxDeForetApiError(f"Could not fetch {url}") from err

        if not isinstance(data, dict):
            raise FeuxDeForetApiError(f"{url} did not return a JSON object")
        return data

    def _normalize_fire(self, item: dict[str, Any]) -> FireAlert:
        """Normalize one feuxdeforet.fr fire object."""
        raw_url = self._string(item.get("url") or item.get("link"))
        raw_thumbnail = self._string(item.get("thumbnail") or item.get("image"))
        position = item.get("position") if isinstance(item.get("position"), dict) else {}
        latitude = self._float(
            item.get("latitude") or item.get("lat") or item.get("y") or position.get("lat")
        )
        longitude = self._float(
            item.get("longitude")
            or item.get("lng")
            or item.get("lon")
            or item.get("x")
            or position.get("lng")
            or position.get("lon")
        )

        return FireAlert(
            id=str(item.get("id") or item.get("slug") or item.get("url") or item.get("title")),
            title=self._string(item.get("title")) or "Incendie",
            commune=self._string(item.get("commune") or item.get("city")),
            department=self._string(item.get("dept") or item.get("department")),
            url=urljoin(DEFAULT_FEUXDEFORET_BASE_URL, raw_url) if raw_url else None,
            date=self._parse_datetime(item.get("dateIso") or item.get("date")),
            active=bool(item.get("enCours", item.get("active", True))),
            thumbnail=urljoin(DEFAULT_FEUXDEFORET_BASE_URL, raw_thumbnail) if raw_thumbnail else None,
            latitude=latitude,
            longitude=longitude,
        )

    async def _async_geocode_alert(self, alert: FireAlert) -> FireAlert:
        """Geocode an alert without native coordinates."""
        if alert.has_location or not alert.commune:
            return alert

        query = f"{alert.commune}, {alert.department or ''}, France".strip()
        if query not in self._geocode_cache:
            self._geocode_cache[query] = await self._async_geocode(query)

        coords = self._geocode_cache[query]
        if coords is None:
            return alert

        return FireAlert(
            **{
                **alert.as_dict(),
                "date": alert.date,
                "latitude": coords[0],
                "longitude": coords[1],
            }
        )

    async def _async_geocode(self, query: str) -> tuple[float, float] | None:
        """Resolve a commune to approximate coordinates."""
        return await _async_geocode_with_session(self._session, query)

    async def async_get_local_weather(self, latitude: float, longitude: float) -> LocalWeather | None:
        """Fetch current local weather for projection heuristics."""
        headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
        params = {
            "latitude": str(latitude),
            "longitude": str(longitude),
            "current": "wind_speed_10m,wind_direction_10m,wind_gusts_10m",
            "wind_speed_unit": "kmh",
            "timezone": "auto",
        }
        try:
            async with self._session.get(
                OPEN_METEO_FORECAST_URL,
                headers=headers,
                params=params,
                timeout=20,
            ) as response:
                if response.status >= 400:
                    _LOGGER.debug("Open-Meteo returned HTTP %s for %s,%s", response.status, latitude, longitude)
                    return None
                data = await response.json(content_type=None)
        except (ClientError, TimeoutError) as err:
            _LOGGER.debug("Could not fetch local weather for %s,%s: %s", latitude, longitude, err)
            return None

        if not isinstance(data, dict):
            return None
        current = data.get("current")
        if not isinstance(current, dict):
            return None
        return LocalWeather(
            latitude=latitude,
            longitude=longitude,
            wind_speed_kmh=self._float(current.get("wind_speed_10m")),
            wind_direction=self._float(current.get("wind_direction_10m")),
            wind_gusts_kmh=self._float(current.get("wind_gusts_10m")),
        )

    async def async_get_fire_hotspots(
        self,
        alert: FireAlert,
        *,
        map_key: str,
        source: str,
        radius_km: float,
        day_range: int,
    ) -> list[FireHotspot]:
        """Fetch NASA FIRMS hotspots near an alert."""
        if not alert.has_location or not map_key or radius_km <= 0:
            return []
        west, south, east, north = _bbox_around(alert.latitude, alert.longitude, radius_km)
        area = f"{west:.5f},{south:.5f},{east:.5f},{north:.5f}"
        url = f"{FIRMS_AREA_URL}/{map_key}/{source}/{area}/{max(1, min(day_range, 5))}"
        headers = {"Accept": "text/csv", "User-Agent": USER_AGENT}
        try:
            async with self._session.get(url, headers=headers, timeout=20) as response:
                if response.status >= 400:
                    _LOGGER.debug("FIRMS returned HTTP %s for %s", response.status, alert.id)
                    return []
                text = await response.text()
        except (ClientError, TimeoutError) as err:
            _LOGGER.debug("Could not fetch FIRMS hotspots for %s: %s", alert.id, err)
            return []

        hotspots: list[FireHotspot] = []
        reader = csv.DictReader(StringIO(text))
        for index, row in enumerate(reader):
            latitude = self._float(row.get("latitude"))
            longitude = self._float(row.get("longitude"))
            if latitude is None or longitude is None:
                continue
            distance = distance_km(alert.latitude, alert.longitude, latitude, longitude)
            if distance > radius_km:
                continue
            hotspots.append(
                FireHotspot(
                    fire_id=alert.id,
                    hotspot_id=f"{alert.id}_{index}",
                    latitude=latitude,
                    longitude=longitude,
                    distance_km=distance,
                    confidence=self._string(row.get("confidence")),
                    brightness=self._float(row.get("bright_ti4") or row.get("brightness")),
                    scan=self._float(row.get("scan")),
                    track=self._float(row.get("track")),
                    acquisition_date=self._string(row.get("acq_date")),
                    acquisition_time=self._string(row.get("acq_time")),
                    satellite=self._string(row.get("satellite")),
                    instrument=self._string(row.get("instrument")),
                )
            )
        hotspots.sort(key=lambda hotspot: hotspot.distance_km)
        return hotspots

    async def async_get_aircraft_positions(self) -> list[AircraftPosition]:
        """Fetch live aircraft and helicopter positions from feuxdeforet.fr."""
        payload = await self._async_get_aircraft_payload()
        items = _aircraft_items(payload)
        aircraft = [self._normalize_aircraft(item) for item in items if isinstance(item, dict)]
        return [item for item in aircraft if item is not None]

    async def _async_get_aircraft_payload(self) -> Any:
        """Request the aircraft tracker payload through the public feuxdeforet.fr proxy."""
        headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
        nonce = await self._async_get_proxy_nonce()
        if nonce:
            headers["X-FDF-Nonce"] = nonce

        for attempt in range(2):
            try:
                async with self._session.get(FEUXDEFORET_AIRCRAFT_URL, headers=headers, timeout=20) as response:
                    if response.status == 403 and attempt == 0:
                        self._proxy_nonce = None
                        nonce = await self._async_get_proxy_nonce()
                        if nonce:
                            headers["X-FDF-Nonce"] = nonce
                        continue
                    if response.status >= 400:
                        raise FeuxDeForetApiError(
                            f"{FEUXDEFORET_AIRCRAFT_URL} returned HTTP {response.status}"
                        )
                    return await response.json(content_type=None)
            except (ClientError, TimeoutError) as err:
                raise FeuxDeForetApiError(f"Could not fetch {FEUXDEFORET_AIRCRAFT_URL}") from err
        return []

    async def _async_get_proxy_nonce(self) -> str | None:
        """Return the public proxy nonce embedded in the feuxdeforet.fr page."""
        if self._proxy_nonce:
            return self._proxy_nonce
        headers = {"Accept": "text/html", "User-Agent": USER_AGENT}
        try:
            async with self._session.get(FEUXDEFORET_HOME_URL, headers=headers, timeout=20) as response:
                if response.status >= 400:
                    return None
                html = await response.text()
        except (ClientError, TimeoutError) as err:
            _LOGGER.debug("Could not fetch feuxdeforet.fr proxy nonce: %s", err)
            return None

        match = re.search(r'"proxyNonce":"([^"]+)"', html)
        self._proxy_nonce = match.group(1) if match else None
        return self._proxy_nonce

    def _normalize_aircraft(self, item: dict[str, Any]) -> AircraftPosition | None:
        """Normalize one aircraft tracker object."""
        track = _aircraft_track(item)
        position = _aircraft_position(item, track)
        if position is None:
            return None

        aircraft_id = self._string(
            _first_value(item, "icao_hex", "icao", "icao24", "fr24_id", "flight_id", "hex", "id")
        )
        if not aircraft_id:
            aircraft_id = self._string(
                _first_value(item, "callsign", "flight", "registration", "reg", "tail_number", "tail")
            )
        if not aircraft_id:
            return None

        category = _aircraft_category(
            self._string(_first_value(item, "categorie", "category", "type", "type_engagement", "moyen"))
        )
        last_position = _last_position_dict(item)
        heading = self._float(
            _first_value(
                last_position or item,
                "heading",
                "heading_deg",
                "course",
                "bearing",
                "cog",
                "track",
            )
        )
        if heading is None:
            heading = _bearing_from_track(track)
        speed_kmh = _speed_kmh(
            last_position or item,
            _first_value(last_position or item, "speed_ms", "speed_kmh", "ground_speed", "gs", "speed_knots", "speed"),
        )
        return AircraftPosition(
            aircraft_id=aircraft_id,
            latitude=position[0],
            longitude=position[1],
            category=category,
            category_label={"dash": "Dash", "heli": "Helicoptere", "canadair": "Canadair"}.get(
                category, "Aeronef"
            ),
            callsign=self._string(_first_value(item, "callsign", "flight", "label")),
            registration=self._string(_first_value(item, "registration", "reg", "tail_number", "tail")),
            description=self._string(_first_value(item, "description", "desc", "aircraft_type")),
            status=self._string(_first_value(item, "status", "etat", "state")),
            first_seen=self._parse_datetime(_first_value(item, "first_seen", "firstSeen", "takeoff_at", "takeoffAt")),
            last_seen=self._parse_datetime(_first_value(item, "last_seen", "lastSeen")),
            last_position_change=self._parse_datetime(_first_value(item, "last_position_change", "lastPositionChange")),
            heading=heading,
            altitude_m=_altitude_m(last_position or item),
            speed_kmh=speed_kmh,
            vertical_rate=self._float(_first_value(last_position or item, "vertical_rate", "verticalRate")),
            squawk=self._string(_first_value(last_position or item, "squawk")),
            track=track,
        )

    @staticmethod
    def _string(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _float(value: Any) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        if not value:
            return None
        text = str(value).replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(text)
        except ValueError:
            return None


async def async_geocode_address(
    hass: HomeAssistant,
    address: str,
    *,
    allow_fallback: bool = True,
) -> tuple[float, float] | None:
    """Resolve a user-entered address to coordinates."""
    session = async_get_clientsession(hass)
    return await _async_geocode_with_session(session, address, allow_fallback=allow_fallback)


async def _async_geocode_with_session(
    session: ClientSession,
    query: str,
    *,
    allow_fallback: bool = True,
) -> tuple[float, float] | None:
    """Resolve a French address or commune to approximate coordinates."""
    if coords := await _async_geocode_adresse_gouv(session, query):
        return coords

    if not allow_fallback:
        return None

    for candidate in _geocode_queries(query):
        if coords := await _async_geocode_nominatim(session, candidate):
            return coords

    return None


async def _async_geocode_adresse_gouv(
    session: ClientSession,
    query: str,
) -> tuple[float, float] | None:
    """Resolve a French address using the official Adresse API."""
    headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
    params = {"q": query, "limit": "1"}
    try:
        async with session.get(
            ADRESSE_GOUV_URL,
            headers=headers,
            params=params,
            timeout=20,
        ) as response:
            if response.status >= 400:
                _LOGGER.debug("Adresse API returned HTTP %s for %s", response.status, query)
                return None
            data = await response.json(content_type=None)
    except (ClientError, TimeoutError) as err:
        _LOGGER.debug("Could not geocode %s with Adresse API: %s", query, err)
        return None

    if not isinstance(data, dict):
        return None
    features = data.get("features")
    if not isinstance(features, list) or not features:
        return None
    first = features[0]
    if not isinstance(first, dict):
        return None
    geometry = first.get("geometry")
    if not isinstance(geometry, dict):
        return None
    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list) or len(coordinates) < 2:
        return None
    longitude = FeuxDeForetClient._float(coordinates[0])
    latitude = FeuxDeForetClient._float(coordinates[1])
    if latitude is None or longitude is None:
        return None
    return latitude, longitude


async def _async_geocode_nominatim(
    session: ClientSession,
    query: str,
) -> tuple[float, float] | None:
    """Resolve a French address or commune using Nominatim."""
    headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
    params = {"q": query, "format": "jsonv2", "limit": "1", "countrycodes": "fr"}
    try:
        async with session.get(
            NOMINATIM_URL,
            headers=headers,
            params=params,
            timeout=20,
        ) as response:
            if response.status >= 400:
                _LOGGER.debug("Nominatim returned HTTP %s for %s", response.status, query)
                return None
            data = await response.json(content_type=None)
    except (ClientError, TimeoutError) as err:
        _LOGGER.debug("Could not geocode %s: %s", query, err)
        return None

    if not isinstance(data, list) or not data:
        return None
    first = data[0]
    latitude = FeuxDeForetClient._float(first.get("lat"))
    longitude = FeuxDeForetClient._float(first.get("lon"))
    if latitude is None or longitude is None:
        return None
    return latitude, longitude


def _geocode_queries(query: str) -> list[str]:
    """Return query variants for tolerant geocoding."""
    clean_query = " ".join(query.replace("\n", " ").split())
    queries = [clean_query]
    if "france" not in clean_query.lower():
        queries.append(f"{clean_query}, France")
    parts = [part.strip() for part in clean_query.split(",") if part.strip()]
    if len(parts) > 1:
        location_parts = parts[:-1] if parts[-1].lower() == "france" else parts
        if location_parts:
            queries.append(location_parts[-1])
        if len(location_parts) > 1:
            queries.append(", ".join(location_parts[-2:]))
    if match := re.search(r"\b(\d{5})\s+([^,]+)", clean_query):
        postcode = match.group(1)
        city = match.group(2).strip()
        queries.append(f"{postcode} {city}")
        queries.append(city)
    return list(dict.fromkeys(queries))


def _bbox_around(latitude: float, longitude: float, radius_km: float) -> tuple[float, float, float, float]:
    """Return west, south, east, north bbox around a point."""
    from math import cos, radians

    lat_delta = radius_km / 111.32
    lon_scale = max(0.01, cos(radians(latitude)))
    lon_delta = radius_km / (111.32 * lon_scale)
    west = max(-180.0, longitude - lon_delta)
    east = min(180.0, longitude + lon_delta)
    south = max(-90.0, latitude - lat_delta)
    north = min(90.0, latitude + lat_delta)
    return west, south, east, north


def _aircraft_items(payload: Any) -> list[Any]:
    """Return aircraft items from accepted payload shapes."""
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []
    for key in ("aircraft", "positions", "data"):
        items = payload.get(key)
        if isinstance(items, list):
            return items
    return []


def _first_value(data: dict[str, Any] | None, *keys: str) -> Any:
    """Return first non-empty value for keys."""
    if not isinstance(data, dict):
        return None
    for key in keys:
        value = data.get(key)
        if value not in (None, ""):
            return value
    return None


def _last_position_dict(item: dict[str, Any]) -> dict[str, Any] | None:
    """Return the last tracker position object when available."""
    for key in ("positions", "path", "track"):
        positions = item.get(key)
        if isinstance(positions, list) and positions:
            last = positions[-1]
            return last if isinstance(last, dict) else None
    for key in ("position", "last_position", "coordinate"):
        position = item.get(key)
        if isinstance(position, dict):
            return position
    return None


def _aircraft_position(
    item: dict[str, Any],
    track: list[tuple[float, float]] | None,
) -> tuple[float, float] | None:
    """Return the aircraft latitude and longitude."""
    position = _last_position_dict(item)
    candidates = [position, item]
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        latitude = FeuxDeForetClient._float(_first_value(candidate, "latitude", "lat"))
        longitude = FeuxDeForetClient._float(_first_value(candidate, "longitude", "lon", "lng"))
        if latitude is not None and longitude is not None:
            return latitude, longitude
    if track:
        return track[-1]
    return None


def _aircraft_track(item: dict[str, Any]) -> list[tuple[float, float]] | None:
    """Return normalized aircraft track points."""
    raw_track = None
    for key in ("positions", "path", "track"):
        value = item.get(key)
        if isinstance(value, list):
            raw_track = value
            break
    if raw_track is None:
        return None

    points: list[tuple[float, float]] = []
    for point in raw_track:
        if isinstance(point, dict):
            latitude = FeuxDeForetClient._float(_first_value(point, "latitude", "lat"))
            longitude = FeuxDeForetClient._float(_first_value(point, "longitude", "lon", "lng"))
        elif isinstance(point, (list, tuple)) and len(point) >= 2:
            latitude = FeuxDeForetClient._float(point[0])
            longitude = FeuxDeForetClient._float(point[1])
        else:
            continue
        if latitude is not None and longitude is not None:
            points.append((latitude, longitude))

    return points or None


def _aircraft_category(raw_category: str | None) -> str:
    """Return normalized aircraft category."""
    text = (raw_category or "").lower()
    if any(key in text for key in ("dragon", "heli", "helico", "helicopter", "h145", "ec45")):
        return "heli"
    if any(key in text for key in ("canadair", "cl415", "cl-415", "cl215", "cl-215")):
        return "canadair"
    if any(key in text for key in ("dash", "q400")):
        return "dash"
    return "aircraft"


def _speed_kmh(data: dict[str, Any] | None, value: Any) -> float | None:
    """Return aircraft speed in km/h."""
    speed = FeuxDeForetClient._float(value)
    if speed is None:
        return None
    if isinstance(data, dict):
        if data.get("speed_kmh") is not None:
            return round(speed, 1)
        if data.get("speed_ms") is not None:
            return round(speed * 3.6, 1)
    return round(speed * 1.852, 1)


def _altitude_m(data: dict[str, Any] | None) -> float | None:
    """Return altitude in meters."""
    if not isinstance(data, dict):
        return None
    raw_value = _first_value(data, "alt_m", "altitude_m", "altitude_baro", "altitude", "alt")
    altitude = FeuxDeForetClient._float(raw_value)
    if altitude is None:
        return None
    if data.get("alt_m") is not None or data.get("altitude_m") is not None:
        return round(altitude, 1)
    if isinstance(raw_value, str) and "m" in raw_value.lower() and "ft" not in raw_value.lower():
        return round(altitude, 1)
    return round(altitude * 0.3048, 1)


def _bearing_from_track(track: list[tuple[float, float]] | None) -> float | None:
    """Return bearing from the last two track points."""
    if not track or len(track) < 2:
        return None
    lat1, lon1 = track[-2]
    lat2, lon2 = track[-1]
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lon = radians(lon2 - lon1)
    y = sin(delta_lon) * cos(lat2_rad)
    x = cos(lat1_rad) * sin(lat2_rad) - sin(lat1_rad) * cos(lat2_rad) * cos(delta_lon)
    return round((degrees(atan2(y, x)) + 360) % 360, 1)
