"""Data models for PyroVeille."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class FireAlert:
    """A normalized fire report from feuxdeforet.fr."""

    id: str
    title: str
    commune: str | None
    department: str | None
    url: str | None
    date: datetime | None
    active: bool
    status: str
    thumbnail: str | None
    latitude: float | None = None
    longitude: float | None = None
    distance_km: float | None = None
    source: str = "feuxdeforet.fr"

    @property
    def has_location(self) -> bool:
        """Return whether this alert has coordinates."""
        return self.latitude is not None and self.longitude is not None

    @property
    def location_name(self) -> str:
        """Return a compact human-readable location."""
        parts = [part for part in (self.commune, self.department) if part]
        return " ".join(parts) if parts else self.title

    def as_dict(self) -> dict[str, object | None]:
        """Return serializable attributes."""
        return {
            "id": self.id,
            "title": self.title,
            "commune": self.commune,
            "department": self.department,
            "url": self.url,
            "date": self.date.isoformat() if self.date else None,
            "active": self.active,
            "status": self.status,
            "thumbnail": self.thumbnail,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "distance_km": self.distance_km,
            "source": self.source,
        }


@dataclass(frozen=True, slots=True)
class FireProjection:
    """Fire progression projection."""

    fire_id: str
    bearing: float
    speed_kmh: float
    horizon_hours: float
    uncertainty_km: float = 0.0
    mode: str = "weather"

    @property
    def distance_km(self) -> float:
        """Return projected distance at horizon."""
        return self.speed_kmh * self.horizon_hours

    def as_dict(self) -> dict[str, object]:
        """Return serializable attributes."""
        return {
            "fire_id": self.fire_id,
            "bearing": self.bearing,
            "speed_kmh": self.speed_kmh,
            "horizon_hours": self.horizon_hours,
            "uncertainty_km": self.uncertainty_km,
            "distance_km": self.distance_km,
            "mode": self.mode,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "FireProjection":
        """Create a projection from stored data."""
        return cls(
            fire_id=str(data["fire_id"]),
            bearing=float(data["bearing"]) % 360,
            speed_kmh=max(0.0, float(data["speed_kmh"])),
            horizon_hours=max(0.0, float(data["horizon_hours"])),
            uncertainty_km=max(0.0, float(data.get("uncertainty_km", 0.0))),
            mode=str(data.get("mode", "weather")),
        )


@dataclass(frozen=True, slots=True)
class LocalWeather:
    """Local weather data used for automatic projections."""

    latitude: float
    longitude: float
    wind_speed_kmh: float | None
    wind_direction: float | None
    wind_gusts_kmh: float | None
    source: str = "open-meteo.com"

    @property
    def downwind_bearing(self) -> float | None:
        """Return downwind direction from meteorological wind direction."""
        if self.wind_direction is None:
            return None
        return (self.wind_direction + 180) % 360

    def as_dict(self) -> dict[str, object | None]:
        """Return serializable attributes."""
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "wind_speed_kmh": self.wind_speed_kmh,
            "wind_direction": self.wind_direction,
            "wind_gusts_kmh": self.wind_gusts_kmh,
            "downwind_bearing": self.downwind_bearing,
            "source": self.source,
        }


@dataclass(frozen=True, slots=True)
class FireHotspot:
    """Satellite active fire detection near a reported fire."""

    fire_id: str
    hotspot_id: str
    latitude: float
    longitude: float
    distance_km: float
    confidence: str | None = None
    brightness: float | None = None
    scan: float | None = None
    track: float | None = None
    acquisition_date: str | None = None
    acquisition_time: str | None = None
    satellite: str | None = None
    instrument: str | None = None
    source: str = "nasa-firms"

    def as_dict(self) -> dict[str, object | None]:
        """Return serializable attributes."""
        return {
            "fire_id": self.fire_id,
            "hotspot_id": self.hotspot_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "distance_km": self.distance_km,
            "confidence": self.confidence,
            "brightness": self.brightness,
            "scan": self.scan,
            "track": self.track,
            "acquisition_date": self.acquisition_date,
            "acquisition_time": self.acquisition_time,
            "satellite": self.satellite,
            "instrument": self.instrument,
            "source": self.source,
        }


@dataclass(frozen=True, slots=True)
class AircraftPosition:
    """Live aircraft position from feuxdeforet.fr."""

    aircraft_id: str
    latitude: float
    longitude: float
    category: str
    category_label: str
    callsign: str | None = None
    registration: str | None = None
    description: str | None = None
    status: str | None = None
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    last_position_change: datetime | None = None
    heading: float | None = None
    altitude_m: float | None = None
    speed_kmh: float | None = None
    vertical_rate: float | None = None
    squawk: str | None = None
    track: list[tuple[float, float]] | None = None
    source: str = "feuxdeforet.fr"

    @property
    def track_geojson(self) -> dict[str, object] | None:
        """Return track as a GeoJSON LineString."""
        if not self.track or len(self.track) < 2:
            return None
        return {
            "type": "Feature",
            "properties": {
                "source": self.source,
                "mode": "aircraft_track",
                "aircraft_id": self.aircraft_id,
                "category": self.category,
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [[round(lon, 6), round(lat, 6)] for lat, lon in self.track],
            },
        }

    def as_dict(self) -> dict[str, object | None]:
        """Return serializable attributes."""
        return {
            "aircraft_id": self.aircraft_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "category": self.category,
            "category_label": self.category_label,
            "callsign": self.callsign,
            "registration": self.registration,
            "description": self.description,
            "status": self.status,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "last_position_change": self.last_position_change.isoformat() if self.last_position_change else None,
            "heading": self.heading,
            "altitude_m": self.altitude_m,
            "speed_kmh": self.speed_kmh,
            "vertical_rate": self.vertical_rate,
            "squawk": self.squawk,
            "track": [[lat, lon] for lat, lon in self.track] if self.track else None,
            "track_geojson": self.track_geojson,
            "source": self.source,
        }
