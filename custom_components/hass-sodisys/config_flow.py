"""Config flow for Sodisys integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from sodisys import Sodisys

from .const import (
    CONF_KINDERGARTEN_ZONE,
    CONF_TIMEZONE,
    CONF_UPDATE_INTERVAL,
    DEFAULT_KINDERGARTEN_ZONE,
    DEFAULT_TIMEZONE,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    ERROR_CANNOT_CONNECT,
    ERROR_INVALID_AUTH,
    ERROR_UNKNOWN,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.data_entry_flow import FlowResult

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_KINDERGARTEN_ZONE, default=DEFAULT_KINDERGARTEN_ZONE): str,
        vol.Optional(CONF_TIMEZONE, default=DEFAULT_TIMEZONE): str,
        vol.Optional(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=60, max=3600)
        ),
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """
    Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    session = async_get_clientsession(hass)
    sodisys = Sodisys(session)

    try:
        await sodisys.login(data[CONF_USERNAME], data[CONF_PASSWORD])
        _LOGGER.info("Successfully authenticated with Sodisys")
    except Exception as err:
        _LOGGER.exception("Failed to authenticate with Sodisys")
        if "auth" in str(err).lower() or "login" in str(err).lower():
            raise InvalidAuthError from err
        raise CannotConnectError from err

    # Return info that you want to store in the config entry.
    return {"title": f"Sodisys ({data[CONF_USERNAME]})"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Sodisys."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> SodisysOptionsFlow:
        """Create the options flow."""
        return SodisysOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnectError:
                errors["base"] = ERROR_CANNOT_CONNECT
            except InvalidAuthError:
                errors["base"] = ERROR_INVALID_AUTH
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = ERROR_UNKNOWN
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnectError(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuthError(HomeAssistantError):
    """Error to indicate there is invalid auth."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_KINDERGARTEN_ZONE,
                        default=self.config_entry.data.get(
                            CONF_KINDERGARTEN_ZONE, DEFAULT_KINDERGARTEN_ZONE
                        ),
                    ): str,
                    vol.Optional(
                        CONF_TIMEZONE,
                        default=self.config_entry.data.get(
                            CONF_TIMEZONE, DEFAULT_TIMEZONE
                        ),
                    ): str,
                    vol.Optional(
                        CONF_UPDATE_INTERVAL,
                        default=self.config_entry.data.get(
                            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=60, max=3600)),
                }
            ),
        )


class SodisysOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Sodisys."""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_KINDERGARTEN_ZONE,
                        default=self.config_entry.options.get(
                            CONF_KINDERGARTEN_ZONE,
                            self.config_entry.data.get(
                                CONF_KINDERGARTEN_ZONE, DEFAULT_KINDERGARTEN_ZONE
                            ),
                        ),
                    ): str,
                    vol.Optional(
                        CONF_TIMEZONE,
                        default=self.config_entry.options.get(
                            CONF_TIMEZONE,
                            self.config_entry.data.get(CONF_TIMEZONE, DEFAULT_TIMEZONE),
                        ),
                    ): str,
                    vol.Optional(
                        CONF_UPDATE_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_UPDATE_INTERVAL,
                            self.config_entry.data.get(
                                CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                            ),
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=60, max=3600)),
                }
            ),
        )
