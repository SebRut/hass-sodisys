"""Support for Sodisys sensors."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_CHECK_IN_TIME,
    ATTR_CHECKED_IN,
    ATTR_CHILD_ID,
    ATTR_LAST_UPDATED,
    ATTR_NAME,
    DOMAIN,
)
from .device import (
    create_child_device_info,
    create_entity_unique_id,
)

if TYPE_CHECKING:
    from datetime import datetime

    from homeassistant.config_entries import ConfigEntry
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from custom_components.sodisys2 import SodisysDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Sodisys sensors from config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []

    @callback
    def async_add_child_sensors() -> None:
        """Add child sensors when data is available."""
        if not coordinator.data:
            return

        new_entities = []
        child_data = coordinator.data
        child_id = child_data[ATTR_CHILD_ID]
        # Check if we already have entities for this child
        existing_checkin = None
        existing_checkout = None

        for entity in entities:
            if hasattr(entity, "child_id") and entity.child_id == child_id:
                if isinstance(entity, SodisysCheckinSensor):
                    existing_checkin = entity
                elif isinstance(entity, SodisysCheckoutSensor):
                    existing_checkout = entity

        # Add check-in sensor if not exists
        if not existing_checkin:
            new_entities.append(SodisysCheckinSensor(coordinator, child_id, child_data))

        # Add check-out sensor if not exists
        if not existing_checkout:
            new_entities.append(
                SodisysCheckoutSensor(coordinator, child_id, child_data)
            )

        if new_entities:
            entities.extend(new_entities)
            async_add_entities(new_entities)

    # Add initial entities
    async_add_child_sensors()

    # Listen for new children
    coordinator.async_add_listener(async_add_child_sensors)


class SodisysBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for Sodisys sensors."""

    def __init__(
        self, coordinator: SodisysDataUpdateCoordinator, child_id: str, child_data: dict
    ) -> None:
        _LOGGER.debug("Initializing SodisysBaseSensor for child %s", child_id)
        _LOGGER.debug("Child data: %s", child_data)
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.child_id = child_id
        self._child_name = child_data.get(ATTR_NAME, f"Child {child_id}")

        # Set device info to group this entity under the child device
        self._attr_device_info = create_child_device_info(child_data)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success and self.coordinator.data is not None
        )


class SodisysCheckinSensor(SodisysBaseSensor):
    """Sensor for child check-in time."""

    def __init__(
        self, coordinator: SodisysDataUpdateCoordinator, child_id: str, child_data: dict
    ) -> None:
        """Initialize the check-in sensor."""
        super().__init__(coordinator, child_id, child_data)

        # Set up entity attributes
        self._attr_unique_id = create_entity_unique_id(child_data, "checkin")
        self._attr_name = f"{self._child_name} Check-in Time"
        self._attr_icon = "mdi:login"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self) -> datetime | None:
        """Return the check-in time."""
        child_data = self.coordinator.data
        return child_data.get("check_in_time")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        child_data = self.coordinator.data

        attributes = {
            "child_id": self.child_id,
            "checked_in": child_data.get(ATTR_CHECKED_IN, False),
        }

        if child_data.get(ATTR_LAST_UPDATED):
            last_updated = child_data[ATTR_LAST_UPDATED]
            if hasattr(last_updated, "isoformat"):
                attributes["last_updated"] = last_updated.isoformat()
            else:
                attributes["last_updated"] = str(last_updated)

        return attributes


class SodisysCheckoutSensor(SodisysBaseSensor):
    """Sensor for child check-out time."""

    def __init__(
        self, coordinator: SodisysDataUpdateCoordinator, child_id: str, child_data: dict
    ) -> None:
        """Initialize the check-out sensor."""
        super().__init__(coordinator, child_id, child_data)

        # Set up entity attributes
        self._attr_unique_id = create_entity_unique_id(child_data, "checkout")
        self._attr_name = f"{self._child_name} Check-out Time"
        self._attr_icon = "mdi:logout"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self) -> datetime | None:
        """Return the check-out time."""
        child_data = self.coordinator.data
        return child_data.get("check_out_time")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        child_data = self.coordinator.data

        attributes = {
            "child_id": self.child_id,
            "checked_in": child_data.get(ATTR_CHECK_IN_TIME, False),
        }

        if child_data.get(ATTR_LAST_UPDATED):
            last_updated = child_data[ATTR_LAST_UPDATED]
            if hasattr(last_updated, "isoformat"):
                attributes["last_updated"] = last_updated.isoformat()
            else:
                attributes["last_updated"] = str(last_updated)

        return attributes
