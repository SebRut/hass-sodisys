"""The Sodisys integration."""

from __future__ import annotations

import datetime
import logging
import zoneinfo
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from sodisys import Sodisys

from .const import (
    ATTR_CHECK_IN_TIME,
    ATTR_CHECK_OUT_TIME,
    ATTR_CHECKED_IN,
    ATTR_CHILD_ID,
    ATTR_LAST_UPDATED,
    ATTR_NAME,
    CONF_TIMEZONE,
    CONF_UPDATE_INTERVAL,
    DEFAULT_TIMEZONE,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from sodisys.rest_api.model import LiveResponse

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.DEVICE_TRACKER, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Sodisys from a config entry."""
    session = async_get_clientsession(hass)
    sodisys = Sodisys(session)

    # Test authentication
    try:
        await sodisys.login(entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD])
    except Exception as err:
        _LOGGER.exception("Failed to authenticate with Sodisys")
        msg = "Authentication failed"
        raise ConfigEntryNotReady(msg) from err

    # Get configuration values, preferring options over data
    update_interval = entry.options.get(
        CONF_UPDATE_INTERVAL,
        entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
    )
    timezone = entry.options.get(
        CONF_TIMEZONE, entry.data.get(CONF_TIMEZONE, DEFAULT_TIMEZONE)
    )

    # Create data update coordinator
    coordinator = SodisysDataUpdateCoordinator(
        hass,
        sodisys,
        update_interval,
        timezone,
    )

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Listen for options updates
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class SodisysDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the Sodisys API."""

    def __init__(
        self,
        hass: HomeAssistant,
        sodisys: Sodisys,
        update_interval: int,
        timezone: str,
    ) -> None:
        """Initialize."""
        self.sodisys = sodisys
        self.timezone_str = timezone

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self) -> dict:
        """Update data via library."""
        try:
            # Fetch live data from Sodisys
            live_response = await self.sodisys.get_live()
            _LOGGER.debug("Fetched live data: %s", live_response)
            return await self._process_live_data(live_response)
        except Exception as err:
            _LOGGER.exception("Error communicating with Sodisys API")
            msg = f"Error communicating with API: {err}"
            raise UpdateFailed(msg) from err

    async def _process_live_data(self, live_response: LiveResponse) -> dict:
        """Process live data from Sodisys into child tracker format."""
        try:
            children_data = {}

            try:
                data_response = await self.sodisys.get_data()
                _LOGGER.debug("data fetched: %s", data_response)
                user_details = data_response.user_details
                children_data[ATTR_CHILD_ID] = user_details.id
                children_data[ATTR_NAME] = (
                    f"{user_details.firstname} {user_details.lastname}"
                )

            except Exception as err:
                _LOGGER.warning("Could not fetch child data: %s", err)
            else:
                if live_response.last_slot is not None:
                    last_slot = live_response.last_slot
                    _LOGGER.debug("Processing last slot: %s", last_slot)

                    tz = datetime.UTC
                    try:
                        tz = zoneinfo.ZoneInfo(self.timezone_str)
                    except zoneinfo.ZoneInfoNotFoundError:
                        _LOGGER.warning(
                            "Could not load timezone %s, using UTC",
                            self.timezone_str,
                        )

                    checked_in = False
                    check_in_time: datetime.datetime | None = None
                    check_out_time: datetime.datetime | None = None

                    if last_slot.in_time is not None:
                        check_in_time = last_slot.get_checkin_timestamp(tz)

                    # Get check-out timestamp
                    if last_slot.out_time is not None:
                        check_out_time = last_slot.get_checkout_timestamp(tz)

                    # Child is checked in if there's a check-in but no check-out
                    if check_in_time is not None and check_out_time is None:
                        checked_in = True

                    children_data[ATTR_CHECKED_IN] = checked_in

                    if check_in_time is not None:
                        children_data[ATTR_CHECK_IN_TIME] = check_in_time

                    if check_out_time is not None:
                        children_data[ATTR_CHECK_OUT_TIME] = check_out_time

            children_data[ATTR_LAST_UPDATED] = datetime.datetime.now(tz=datetime.UTC)

        except Exception as err:
            _LOGGER.exception("Error processing live data")
            msg = f"Error processing live data: {err}"
            raise UpdateFailed(msg) from err
        else:
            return children_data
