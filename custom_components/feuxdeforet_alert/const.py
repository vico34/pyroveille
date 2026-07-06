"""Constants for Feux de Foret Alert."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "feuxdeforet_alert"

DEFAULT_NAME = "PyroVeille"
DEFAULT_API_BASE_URL = "https://feuxdeforet.fr/api"
DEFAULT_FEUXDEFORET_BASE_URL = "https://feuxdeforet.fr"
DEFAULT_SCAN_INTERVAL = timedelta(minutes=5)
DEFAULT_RADIUS_KM = 30.0
DEFAULT_MAX_ITEMS = 50
DEFAULT_CREATE_PERSISTENT_NOTIFICATIONS = True
DEFAULT_GEOCODE_MISSING_COORDINATES = True
DEFAULT_ONLY_ACTIVE = True

CONF_CENTER_LATITUDE = "center_latitude"
CONF_CENTER_LONGITUDE = "center_longitude"
CONF_RADIUS_KM = "radius_km"
CONF_DEPARTMENTS = "departments"
CONF_ONLY_ACTIVE = "only_active"
CONF_CREATE_PERSISTENT_NOTIFICATIONS = "create_persistent_notifications"
CONF_GEOCODE_MISSING_COORDINATES = "geocode_missing_coordinates"
CONF_API_BASE_URL = "api_base_url"

EVENT_NEARBY_FIRE = f"{DOMAIN}_nearby_fire"

PLATFORMS = ["binary_sensor", "sensor", "device_tracker"]
