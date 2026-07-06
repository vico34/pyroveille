"""Client for public feuxdeforet.fr data."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from urllib.parse import urljoin

from aiohttp import ClientError, ClientSession
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DEFAULT_FEUXDEFORET_BASE_URL, DEFAULT_MAX_ITEMS
from .models import FireAlert

_LOGGER = logging.getLogger(__name__)

USER_AGENT = "HomeAssistant-FeuxDeForetAlert/0.1"
ADRESSE_GOUV_URL = "https://api-adresse.data.gouv.fr/search/"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


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


async def async_geocode_address(hass: HomeAssistant, address: str) -> tuple[float, float] | None:
    """Resolve a user-entered address to coordinates."""
    session = async_get_clientsession(hass)
    return await _async_geocode_with_session(session, address)


async def _async_geocode_with_session(
    session: ClientSession,
    query: str,
) -> tuple[float, float] | None:
    """Resolve a French address or commune to approximate coordinates."""
    if coords := await _async_geocode_adresse_gouv(session, query):
        return coords

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
    return list(dict.fromkeys(queries))
