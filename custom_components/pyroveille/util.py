"""Utility helpers for PyroVeille."""

from __future__ import annotations

from math import asin, atan2, cos, degrees, radians, sin, sqrt


def parse_departments(value: str | list[str] | tuple[str, ...] | None) -> set[str]:
    """Parse a department filter value."""
    if not value:
        return set()
    if isinstance(value, str):
        raw_items = value.replace(";", ",").split(",")
    else:
        raw_items = list(value)
    return {str(item).strip().upper().zfill(2) for item in raw_items if str(item).strip()}


def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance in kilometers."""
    radius = 6371.0088
    phi1 = radians(lat1)
    phi2 = radians(lat2)
    delta_phi = radians(lat2 - lat1)
    delta_lambda = radians(lon2 - lon1)
    a = sin(delta_phi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(delta_lambda / 2) ** 2
    return 2 * radius * asin(sqrt(a))


def destination_point(latitude: float, longitude: float, bearing: float, distance: float) -> tuple[float, float]:
    """Return destination coordinates from a start point, bearing and distance."""
    radius = 6371.0088
    angular_distance = distance / radius
    bearing_rad = radians(bearing)
    lat1 = radians(latitude)
    lon1 = radians(longitude)

    lat2 = asin(
        sin(lat1) * cos(angular_distance)
        + cos(lat1) * sin(angular_distance) * cos(bearing_rad)
    )
    lon2 = lon1 + atan2(
        sin(bearing_rad) * sin(angular_distance) * cos(lat1),
        cos(angular_distance) - sin(lat1) * sin(lat2),
    )
    return degrees(lat2), ((degrees(lon2) + 540) % 360) - 180
