"""The Sodisys integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from aiohttp import ClientSession
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_TIMEZONE,
    CONF_UPDATE_INTERVAL,
    DEFAULT_TIMEZONE,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.DEVICE_TRACKER, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Sodisys from a config entry."""
    try:
        from sodisys import Sodisys
    except ImportError:
        _LOGGER.error(
            "Sodisys package not found. Please install it using: pip install sodisys")
        raise ConfigEntryNotReady("Sodisys package not installed") from None

    session = async_get_clientsession(hass)
    sodisys = Sodisys(session)

    # Test authentication
    try:
        await sodisys.login(entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD])
    except Exception as err:
        _LOGGER.error("Failed to authenticate with Sodisys: %s", err)
        raise ConfigEntryNotReady("Authentication failed") from err

    # Get configuration values, preferring options over data
    update_interval = entry.options.get(
        CONF_UPDATE_INTERVAL,
        entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
    )
    timezone = entry.options.get(
        CONF_TIMEZONE,
        entry.data.get(CONF_TIMEZONE, DEFAULT_TIMEZONE)
    )

    # Create data update coordinator
    coordinator = SodisysDataUpdateCoordinator(
        hass,
        sodisys,
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
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
        sodisys,
        username: str,
        password: str,
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

    async def _async_update_data(self):
        """Update data via library."""
        try:
            # Fetch live data from Sodisys
            live_response = await self.sodisys.get_live()
            children_data = await self._process_live_data(live_response)
            return children_data

        except Exception as err:
            _LOGGER.error("Error communicating with Sodisys API: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    async def _process_live_data(self, live_responses):
        """Process live data from Sodisys into child tracker format."""
        import datetime

        try:
            children_data = {}

            # live_responses should be a dict with child_id as keys and LiveResponse as values
            # or a single LiveResponse if only one child
            if not isinstance(live_responses, dict):
                # If it's a single response, we need to handle it differently
                # This assumes the response structure - you may need to adjust
                _LOGGER.warning(
                    "Unexpected live response format: %s", type(live_responses))
                return {}

            # Fetch child data to get names and IDs
            child_data_map = {}
            try:
                data_response = await self.sodisys.get_data()
                if hasattr(data_response, 'user_details'):
                    # For single child account
                    user_details = data_response.user_details
                    child_data_map['default'] = {
                        'id': getattr(user_details, 'id', 'default'),
                        'name': f"{user_details.firstname} {user_details.lastname}"
                    }
                elif isinstance(data_response, dict):
                    # For multiple children - assuming dict with child_id as keys
                    for child_id, data in data_response.items():
                        if hasattr(data, 'user_details'):
                            user_details = data.user_details
                            child_data_map[child_id] = {
                                'id': getattr(user_details, 'id', child_id),
                                'name': f"{user_details.firstname} {user_details.lastname}"
                            }
            except Exception as err:
                _LOGGER.warning("Could not fetch child data: %s", err)

            for child_id, live_response in live_responses.items():
                if live_response is None:
                    continue

                # Extract data from LiveResponse
                # Get child data from data response or fallback to generic data
                child_info = child_data_map.get(
                    child_id) or child_data_map.get('default')
                if child_info:
                    unique_id = child_info['id']
                    child_name = child_info['name']
                else:
                    unique_id = child_id
                    child_name = f"Child {child_id}"

                # Determine if child is currently checked in
                checked_in = False
                check_in_time = None
                check_out_time = None

                if live_response.last_slot is not None:
                    last_slot = live_response.last_slot

                    # Get configured timezone for kindergarten
                    try:
                        import zoneinfo
                        tz = zoneinfo.ZoneInfo(self.timezone_str)
                    except Exception:
                        try:
                            # Fallback for older Python versions
                            import pytz
                            tz = pytz.timezone(self.timezone_str)
                        except Exception:
                            _LOGGER.warning(
                                "Could not load timezone %s, using UTC", self.timezone_str)
                            tz = datetime.timezone.utc

                    # Get check-in timestamp
                    if last_slot.in_time is not None:
                        check_in_time = last_slot.get_checkin_timestamp(tz)

                    # Get check-out timestamp
                    if last_slot.out_time is not None:
                        check_out_time = last_slot.get_checkout_timestamp(tz)

                    # Child is checked in if there's a check-in time but no check-out time
                    # or if check-out time is earlier than check-in time (same day)
                    if check_in_time is not None:
                        if check_out_time is None:
                            checked_in = True
                        elif check_in_time > check_out_time:
                            checked_in = True

                children_data[child_id] = {
                    'id': child_id,
                    'unique_id': unique_id,
                    'name': child_name,
                    'checked_in': checked_in,
                    'check_in_time': check_in_time,
                    'check_out_time': check_out_time,
                    'last_updated': datetime.datetime.now(),
                }

            return children_data

        except Exception as err:
            _LOGGER.error("Error processing live data: %s", err)
            raise UpdateFailed(f"Error processing live data: {err}") from err
