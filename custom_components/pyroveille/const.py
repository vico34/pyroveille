"""Constants for PyroVeille."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "pyroveille"

DEFAULT_NAME = "PyroVeille"
DEFAULT_API_BASE_URL = "https://feuxdeforet.fr/api"
DEFAULT_FEUXDEFORET_BASE_URL = "https://feuxdeforet.fr"
DEFAULT_SCAN_INTERVAL = timedelta(minutes=5)
DEFAULT_ADDRESS = "France"
DEFAULT_RADIUS_KM = 30.0
DEFAULT_MAX_ITEMS = 50
DEFAULT_CREATE_PERSISTENT_NOTIFICATIONS = True
DEFAULT_CREATE_TELEGRAM_NOTIFICATIONS = False
DEFAULT_GEOCODE_MISSING_COORDINATES = True
DEFAULT_INCLUDE_LINK_IN_NOTIFICATIONS = True
DEFAULT_NOTIFICATION_MAX_DISTANCE_KM = 0.0
DEFAULT_ONLY_ACTIVE = True
DEFAULT_TELEGRAM_NOTIFY_SERVICE = "telegram"

GEOCODING_MODE_OFFICIAL = "official"
GEOCODING_MODE_FALLBACK = "fallback"
GEOCODING_MODES = [GEOCODING_MODE_FALLBACK, GEOCODING_MODE_OFFICIAL]

CONF_ADDRESS = "address"
CONF_CENTER_LATITUDE = "center_latitude"
CONF_CENTER_LONGITUDE = "center_longitude"
CONF_RADIUS_KM = "radius_km"
CONF_DEPARTMENTS = "departments"
CONF_ONLY_ACTIVE = "only_active"
CONF_CREATE_PERSISTENT_NOTIFICATIONS = "create_persistent_notifications"
CONF_CREATE_TELEGRAM_NOTIFICATIONS = "create_telegram_notifications"
CONF_TELEGRAM_NOTIFY_SERVICE = "telegram_notify_service"
CONF_GEOCODE_MISSING_COORDINATES = "geocode_missing_coordinates"
CONF_ADDRESS_GEOCODING_MODE = "address_geocoding_mode"
CONF_INCLUDE_LINK_IN_NOTIFICATIONS = "include_link_in_notifications"
CONF_NOTIFICATION_MAX_DISTANCE_KM = "notification_max_distance_km"
CONF_API_BASE_URL = "api_base_url"

EVENT_NEARBY_FIRE = f"{DOMAIN}_nearby_fire"

PLATFORMS = ["binary_sensor", "sensor", "device_tracker"]
