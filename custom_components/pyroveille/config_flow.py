"""Config flow for PyroVeille."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .api import async_geocode_address
from .const import (
    CONF_ADDRESS,
    CONF_ADDRESS_GEOCODING_MODE,
    CONF_API_BASE_URL,
    CONF_CENTER_LATITUDE,
    CONF_CENTER_LONGITUDE,
    CONF_CREATE_PERSISTENT_NOTIFICATIONS,
    CONF_CREATE_TELEGRAM_NOTIFICATIONS,
    CONF_DEPARTMENTS,
    CONF_ENABLE_PROJECTIONS,
    CONF_GEOCODE_MISSING_COORDINATES,
    CONF_INCLUDE_LINK_IN_NOTIFICATIONS,
    CONF_NOTIFICATION_MAX_DISTANCE_KM,
    CONF_ONLY_ACTIVE,
    CONF_RADIUS_KM,
    CONF_TELEGRAM_NOTIFY_SERVICE,
    DEFAULT_API_BASE_URL,
    DEFAULT_ADDRESS,
    DEFAULT_CREATE_PERSISTENT_NOTIFICATIONS,
    DEFAULT_CREATE_TELEGRAM_NOTIFICATIONS,
    DEFAULT_ENABLE_PROJECTIONS,
    DEFAULT_GEOCODE_MISSING_COORDINATES,
    DEFAULT_INCLUDE_LINK_IN_NOTIFICATIONS,
    DEFAULT_NAME,
    DEFAULT_NOTIFICATION_MAX_DISTANCE_KM,
    DEFAULT_ONLY_ACTIVE,
    DEFAULT_RADIUS_KM,
    DEFAULT_TELEGRAM_NOTIFY_SERVICE,
    DOMAIN,
    GEOCODING_MODE_FALLBACK,
    GEOCODING_MODE_OFFICIAL,
)
from .util import parse_departments


class FeuxDeForetConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            coords: tuple[float, float] | None = None
            address = str(user_input.get(CONF_ADDRESS, "")).strip()
            _normalize_telegram_target(user_input)
            if not address:
                errors[CONF_ADDRESS] = "invalid_address"
            if user_input.get(CONF_CREATE_TELEGRAM_NOTIFICATIONS) and not user_input.get(CONF_TELEGRAM_NOTIFY_SERVICE):
                errors[CONF_TELEGRAM_NOTIFY_SERVICE] = "invalid_notify_service"
            try:
                radius_km = float(user_input[CONF_RADIUS_KM])
            except (TypeError, ValueError):
                radius_km = 0
            if radius_km <= 0:
                errors[CONF_RADIUS_KM] = "invalid_radius"
            if _notification_distance(user_input) < 0:
                errors[CONF_NOTIFICATION_MAX_DISTANCE_KM] = "invalid_notification_distance"

            if not errors:
                coords = await async_geocode_address(
                    self.hass,
                    address,
                    allow_fallback=user_input.get(CONF_ADDRESS_GEOCODING_MODE) != GEOCODING_MODE_OFFICIAL,
                )
                if coords is None:
                    errors[CONF_ADDRESS] = "address_not_found"

            if not errors:
                await self.async_set_unique_id("default")
                self._abort_if_unique_id_configured()
                user_input[CONF_ADDRESS] = address
                user_input[CONF_CENTER_LATITUDE] = coords[0]
                user_input[CONF_CENTER_LONGITUDE] = coords[1]
                user_input[CONF_DEPARTMENTS] = ",".join(sorted(parse_departments(user_input.get(CONF_DEPARTMENTS))))
                return self.async_create_entry(title=DEFAULT_NAME, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(user_input or {}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> FeuxDeForetOptionsFlow:
        """Create options flow."""
        return FeuxDeForetOptionsFlow(config_entry)


class FeuxDeForetOptionsFlow(config_entries.OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Manage options."""
        errors: dict[str, str] = {}
        if user_input is not None:
            coords: tuple[float, float] | None = None
            address = str(user_input.get(CONF_ADDRESS, "")).strip()
            _normalize_telegram_target(user_input)
            if not address:
                errors[CONF_ADDRESS] = "invalid_address"
            if user_input.get(CONF_CREATE_TELEGRAM_NOTIFICATIONS) and not user_input.get(CONF_TELEGRAM_NOTIFY_SERVICE):
                errors[CONF_TELEGRAM_NOTIFY_SERVICE] = "invalid_notify_service"
            try:
                radius_km = float(user_input[CONF_RADIUS_KM])
            except (TypeError, ValueError):
                radius_km = 0
            if radius_km <= 0:
                errors[CONF_RADIUS_KM] = "invalid_radius"
            if _notification_distance(user_input) < 0:
                errors[CONF_NOTIFICATION_MAX_DISTANCE_KM] = "invalid_notification_distance"
            if not errors:
                coords = await async_geocode_address(
                    self.hass,
                    address,
                    allow_fallback=user_input.get(CONF_ADDRESS_GEOCODING_MODE) != GEOCODING_MODE_OFFICIAL,
                )
                if coords is None:
                    errors[CONF_ADDRESS] = "address_not_found"

            if not errors:
                user_input[CONF_ADDRESS] = address
                user_input[CONF_CENTER_LATITUDE] = coords[0]
                user_input[CONF_CENTER_LONGITUDE] = coords[1]
                user_input[CONF_DEPARTMENTS] = ",".join(sorted(parse_departments(user_input.get(CONF_DEPARTMENTS))))
                return self.async_create_entry(title="", data=user_input)

        defaults = {**self._config_entry.data, **self._config_entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=_schema(defaults),
            errors=errors,
        )


def _schema(defaults: dict[str, Any], *, include_center: bool = True) -> vol.Schema:
    """Return flow schema."""
    fields: dict[Any, Any] = {}
    if include_center:
        fields[
            vol.Required(
                CONF_ADDRESS,
                default=defaults.get(CONF_ADDRESS, DEFAULT_ADDRESS),
            )
        ] = selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT))
        fields[
            vol.Required(
                CONF_ADDRESS_GEOCODING_MODE,
                default=defaults.get(CONF_ADDRESS_GEOCODING_MODE, GEOCODING_MODE_FALLBACK),
            )
        ] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    selector.SelectOptionDict(value=GEOCODING_MODE_FALLBACK, label="Adresse puis commune"),
                    selector.SelectOptionDict(value=GEOCODING_MODE_OFFICIAL, label="Adresse stricte"),
                ],
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        )

    fields[
        vol.Required(CONF_RADIUS_KM, default=defaults.get(CONF_RADIUS_KM, DEFAULT_RADIUS_KM))
    ] = selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=1,
            max=500,
            step=1,
            unit_of_measurement="km",
            mode=selector.NumberSelectorMode.SLIDER,
        )
    )
    fields[vol.Optional(CONF_DEPARTMENTS, default=defaults.get(CONF_DEPARTMENTS, ""))] = str
    fields[vol.Required(CONF_ONLY_ACTIVE, default=defaults.get(CONF_ONLY_ACTIVE, DEFAULT_ONLY_ACTIVE))] = bool
    fields[
        vol.Required(
            CONF_CREATE_PERSISTENT_NOTIFICATIONS,
            default=defaults.get(
                CONF_CREATE_PERSISTENT_NOTIFICATIONS,
                DEFAULT_CREATE_PERSISTENT_NOTIFICATIONS,
            ),
        )
    ] = bool
    fields[
        vol.Required(
            CONF_NOTIFICATION_MAX_DISTANCE_KM,
            default=defaults.get(CONF_NOTIFICATION_MAX_DISTANCE_KM, DEFAULT_NOTIFICATION_MAX_DISTANCE_KM),
        )
    ] = selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=0,
            max=500,
            step=1,
            unit_of_measurement="km",
            mode=selector.NumberSelectorMode.BOX,
        )
    )
    fields[
        vol.Required(
            CONF_INCLUDE_LINK_IN_NOTIFICATIONS,
            default=defaults.get(CONF_INCLUDE_LINK_IN_NOTIFICATIONS, DEFAULT_INCLUDE_LINK_IN_NOTIFICATIONS),
        )
    ] = bool
    fields[
        vol.Required(
            CONF_CREATE_TELEGRAM_NOTIFICATIONS,
            default=defaults.get(CONF_CREATE_TELEGRAM_NOTIFICATIONS, DEFAULT_CREATE_TELEGRAM_NOTIFICATIONS),
        )
    ] = bool
    fields[
        vol.Optional(
            CONF_TELEGRAM_NOTIFY_SERVICE,
            default=defaults.get(CONF_TELEGRAM_NOTIFY_SERVICE, DEFAULT_TELEGRAM_NOTIFY_SERVICE),
        )
    ] = selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT))
    fields[
        vol.Required(
            CONF_GEOCODE_MISSING_COORDINATES,
            default=defaults.get(CONF_GEOCODE_MISSING_COORDINATES, DEFAULT_GEOCODE_MISSING_COORDINATES),
        )
    ] = bool
    fields[
        vol.Required(
            CONF_ENABLE_PROJECTIONS,
            default=defaults.get(CONF_ENABLE_PROJECTIONS, DEFAULT_ENABLE_PROJECTIONS),
        )
    ] = bool
    fields[vol.Required(CONF_API_BASE_URL, default=defaults.get(CONF_API_BASE_URL, DEFAULT_API_BASE_URL))] = str
    return vol.Schema(fields)


def _normalize_telegram_target(user_input: dict[str, Any]) -> None:
    """Normalize the Telegram notify target in-place."""
    user_input[CONF_TELEGRAM_NOTIFY_SERVICE] = str(user_input.get(CONF_TELEGRAM_NOTIFY_SERVICE, "")).strip()


def _notification_distance(user_input: dict[str, Any]) -> float:
    """Return configured notification distance threshold."""
    try:
        return float(user_input.get(CONF_NOTIFICATION_MAX_DISTANCE_KM, DEFAULT_NOTIFICATION_MAX_DISTANCE_KM))
    except (TypeError, ValueError):
        return -1
