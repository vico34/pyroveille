"""Config flow for Feux de Foret Alert."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_API_BASE_URL,
    CONF_CENTER_LATITUDE,
    CONF_CENTER_LONGITUDE,
    CONF_CREATE_PERSISTENT_NOTIFICATIONS,
    CONF_DEPARTMENTS,
    CONF_GEOCODE_MISSING_COORDINATES,
    CONF_ONLY_ACTIVE,
    CONF_RADIUS_KM,
    DEFAULT_API_BASE_URL,
    DEFAULT_CREATE_PERSISTENT_NOTIFICATIONS,
    DEFAULT_GEOCODE_MISSING_COORDINATES,
    DEFAULT_NAME,
    DEFAULT_ONLY_ACTIVE,
    DEFAULT_RADIUS_KM,
    DOMAIN,
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
            if not -90 <= float(user_input[CONF_CENTER_LATITUDE]) <= 90:
                errors[CONF_CENTER_LATITUDE] = "invalid_latitude"
            if not -180 <= float(user_input[CONF_CENTER_LONGITUDE]) <= 180:
                errors[CONF_CENTER_LONGITUDE] = "invalid_longitude"
            if float(user_input[CONF_RADIUS_KM]) <= 0:
                errors[CONF_RADIUS_KM] = "invalid_radius"

            if not errors:
                await self.async_set_unique_id("default")
                self._abort_if_unique_id_configured()
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
            if float(user_input[CONF_RADIUS_KM]) <= 0:
                errors[CONF_RADIUS_KM] = "invalid_radius"
            if not errors:
                user_input[CONF_DEPARTMENTS] = ",".join(sorted(parse_departments(user_input.get(CONF_DEPARTMENTS))))
                return self.async_create_entry(title="", data=user_input)

        defaults = {**self._config_entry.data, **self._config_entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=_schema(defaults, include_center=False),
            errors=errors,
        )


def _schema(defaults: dict[str, Any], *, include_center: bool = True) -> vol.Schema:
    """Return flow schema."""
    fields: dict[Any, Any] = {}
    if include_center:
        fields[
            vol.Required(
                CONF_CENTER_LATITUDE,
                default=defaults.get(CONF_CENTER_LATITUDE, 46.603354),
            )
        ] = selector.NumberSelector(selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX))
        fields[
            vol.Required(
                CONF_CENTER_LONGITUDE,
                default=defaults.get(CONF_CENTER_LONGITUDE, 1.888334),
            )
        ] = selector.NumberSelector(selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX))

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
            CONF_GEOCODE_MISSING_COORDINATES,
            default=defaults.get(CONF_GEOCODE_MISSING_COORDINATES, DEFAULT_GEOCODE_MISSING_COORDINATES),
        )
    ] = bool
    fields[vol.Required(CONF_API_BASE_URL, default=defaults.get(CONF_API_BASE_URL, DEFAULT_API_BASE_URL))] = str
    return vol.Schema(fields)
