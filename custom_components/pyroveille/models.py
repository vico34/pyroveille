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
            "thumbnail": self.thumbnail,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "distance_km": self.distance_km,
            "source": self.source,
        }


@dataclass(frozen=True, slots=True)
class FireProjection:
    """User-defined fire progression projection."""

    fire_id: str
    bearing: float
    speed_kmh: float
    horizon_hours: float
    uncertainty_km: float = 0.0

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
        )
