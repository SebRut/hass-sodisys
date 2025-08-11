"""Support for Sodisys device tracker."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_CHECK_IN_TIME,
    ATTR_CHECK_OUT_TIME,
    ATTR_CHECKED_IN,
    ATTR_CHILD_ID,
    ATTR_LAST_UPDATED,
    ATTR_NAME,
    CONF_KINDERGARTEN_ZONE,
    DEFAULT_KINDERGARTEN_ZONE,
    DOMAIN,
    STATE_NOT_HOME,
)
from .device import (
    create_child_device_info,
    create_entity_unique_id,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from custom_components.sodisys2 import SodisysDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Sodisys device tracker from config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    kindergarten_zone = config_entry.options.get(
        CONF_KINDERGARTEN_ZONE,
        config_entry.data.get(CONF_KINDERGARTEN_ZONE, DEFAULT_KINDERGARTEN_ZONE),
    )

    entities = []

    @callback
    def async_add_child_trackers() -> None:
        """Add child trackers when data is available."""
        if not coordinator.data:
            return

        new_entities = []
        child_data = coordinator.data
        child_id = child_data[ATTR_CHILD_ID]

        # Check if we already have an entity for this child
        existing_entity = None
        for entity in entities:
            if entity.child_id == child_id:
                existing_entity = entity
                break

        if not existing_entity:
            new_entities.append(
                SodisysChildTracker(
                    coordinator, child_id, child_data, kindergarten_zone
                )
            )

        if new_entities:
            entities.extend(new_entities)
            async_add_entities(new_entities)

    # Add initial entities
    async_add_child_trackers()

    # Listen for new children
    coordinator.async_add_listener(async_add_child_trackers)


class SodisysChildTracker(CoordinatorEntity, TrackerEntity):
    """Representation of a Sodisys child tracker."""

    def __init__(
        self,
        coordinator: SodisysDataUpdateCoordinator,
        child_id: str,
        child_data: dict,
        kindergarten_zone: str,
    ) -> None:
        """Initialize the tracker."""
        super().__init__(coordinator)
        self.child_id = child_id
        self._kindergarten_zone = kindergarten_zone
        self._child_name = child_data.get(ATTR_NAME, f"Child {child_id}")

        # Set up entity attributes using utility functions
        self._attr_unique_id = create_entity_unique_id(child_data, "tracker")
        self._attr_name = f"{self._child_name} Location"
        self._attr_icon = "mdi:map-marker-account"

        # Set device info to group this entity under the child device
        self._attr_device_info = create_child_device_info(child_data)

    @property
    def source_type(self) -> SourceType:
        """Return the source type of the device."""
        return SourceType.ROUTER

    @property
    def location_name(self) -> str | None:
        """Return a location name for the current location of the device."""
        child_data = self.coordinator.data
        if child_data.get(ATTR_CHECKED_IN, False):
            return self._kindergarten_zone
        return STATE_NOT_HOME

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the device state attributes."""
        if not self.coordinator.data or self.child_id not in self.coordinator.data:
            return {}

        child_data = self.coordinator.data

        attributes = {
            ATTR_CHILD_ID: self.child_id,
        }

        # Format datetime attributes for display
        if child_data.get(ATTR_CHECK_IN_TIME):
            check_in_time = child_data[ATTR_CHECK_IN_TIME]
            if hasattr(check_in_time, "isoformat"):
                attributes[ATTR_CHECK_IN_TIME] = check_in_time.isoformat()
            else:
                attributes[ATTR_CHECK_IN_TIME] = str(check_in_time)

        if child_data.get(ATTR_CHECK_OUT_TIME):
            check_out_time = child_data[ATTR_CHECK_OUT_TIME]
            if hasattr(check_out_time, "isoformat"):
                attributes[ATTR_CHECK_OUT_TIME] = check_out_time.isoformat()
            else:
                attributes[ATTR_CHECK_OUT_TIME] = str(check_out_time)

        if child_data.get(ATTR_LAST_UPDATED):
            last_updated = child_data[ATTR_LAST_UPDATED]
            if hasattr(last_updated, "isoformat"):
                attributes[ATTR_LAST_UPDATED] = last_updated.isoformat()
            else:
                attributes[ATTR_LAST_UPDATED] = str(last_updated)

        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success and self.coordinator.data is not None
        )

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        # Device info is set in __init__ and stored in _attr_device_info
        # Update with current data if available
        current_data = self.coordinator.data
        # Update device info with current data if name changed
        return create_child_device_info(current_data)
