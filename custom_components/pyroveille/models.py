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
