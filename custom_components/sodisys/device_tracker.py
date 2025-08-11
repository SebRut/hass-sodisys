"""Support for Sodisys device tracker."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_CHECK_IN_TIME,
    ATTR_CHECK_OUT_TIME,
    ATTR_CHILD_ID,
    ATTR_LAST_UPDATED,
    CONF_KINDERGARTEN_ZONE,
    DEFAULT_KINDERGARTEN_ZONE,
    DOMAIN,
    STATE_NOT_HOME,
)
from .device import (
    create_child_device_info,
    create_entity_unique_id,
)

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
        config_entry.data.get(CONF_KINDERGARTEN_ZONE,
                              DEFAULT_KINDERGARTEN_ZONE)
    )

    entities = []

    @callback
    def async_add_child_trackers():
        """Add child trackers when data is available."""
        if not coordinator.data:
            return

        new_entities = []
        for child_id, child_data in coordinator.data.items():
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

    def __init__(self, coordinator, child_id: str, child_data: dict, kindergarten_zone: str) -> None:
        """Initialize the tracker."""
        super().__init__(coordinator)
        self.child_id = child_id
        self._kindergarten_zone = kindergarten_zone
        self._child_name = child_data.get("name", f"Child {child_id}")

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
        if not self.coordinator.data or self.child_id not in self.coordinator.data:
            return STATE_NOT_HOME

        child_data = self.coordinator.data[self.child_id]
        if child_data.get("checked_in", False):
            return self._kindergarten_zone
        return STATE_NOT_HOME

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the device state attributes."""
        if not self.coordinator.data or self.child_id not in self.coordinator.data:
            return {}

        child_data = self.coordinator.data[self.child_id]

        attributes = {
            ATTR_CHILD_ID: self.child_id,
        }

        # Format datetime attributes for display
        if child_data.get("check_in_time"):
            check_in_time = child_data["check_in_time"]
            if hasattr(check_in_time, 'isoformat'):
                attributes[ATTR_CHECK_IN_TIME] = check_in_time.isoformat()
            else:
                attributes[ATTR_CHECK_IN_TIME] = str(check_in_time)

        if child_data.get("check_out_time"):
            check_out_time = child_data["check_out_time"]
            if hasattr(check_out_time, 'isoformat'):
                attributes[ATTR_CHECK_OUT_TIME] = check_out_time.isoformat()
            else:
                attributes[ATTR_CHECK_OUT_TIME] = str(check_out_time)

        if child_data.get("last_updated"):
            last_updated = child_data["last_updated"]
            if hasattr(last_updated, 'isoformat'):
                attributes[ATTR_LAST_UPDATED] = last_updated.isoformat()
            else:
                attributes[ATTR_LAST_UPDATED] = str(last_updated)

        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self.child_id in self.coordinator.data
        )

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        # Device info is set in __init__ and stored in _attr_device_info
        # Update with current data if available
        if self.coordinator.data and self.child_id in self.coordinator.data:
            current_data = self.coordinator.data[self.child_id]
            # Update device info with current data if name changed
            return create_child_device_info(current_data)

        return self._attr_device_info
