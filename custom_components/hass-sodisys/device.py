"""Device utilities for Sodisys integration."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo

from .const import (
    ATTR_CHILD_ID,
    DEVICE_MANUFACTURER,
    DEVICE_MODEL_CHILD,
    DEVICE_SW_VERSION,
    DOMAIN,
)


def create_child_device_info(child_data: dict[str, Any]) -> DeviceInfo:
    """
    Create device info for a child device.

    Args:
        child_data: Dictionary containing child information with keys:
            - unique_id: Unique identifier for the child (from UserDetails.id)
            - name: Child's full name (from UserDetails.firstname + lastname)
            - id: Child ID used internally by Sodisys

    Returns:
        DeviceInfo dictionary for Home Assistant device registry

    """
    unique_id = child_data.get("unique_id", child_data.get(ATTR_CHILD_ID, "unknown"))
    child_name = child_data.get("name", f"Child {unique_id}")

    return DeviceInfo(
        identifiers={(DOMAIN, f"child_{unique_id}")},
        name=child_name,
        manufacturer=DEVICE_MANUFACTURER,
        model=DEVICE_MODEL_CHILD,
        sw_version=DEVICE_SW_VERSION,
    )


def get_child_device_identifier(child_data: dict[str, Any]) -> str:
    """
    Get the device identifier for a child.

    Args:
        child_data: Dictionary containing child information

    Returns:
        Device identifier string used in Home Assistant device registry

    """
    unique_id = child_data.get("unique_id", child_data.get(ATTR_CHILD_ID, "unknown"))
    return f"child_{unique_id}"


def create_entity_unique_id(child_data: dict[str, Any], entity_type: str) -> str:
    """
    Create a unique entity ID for a child entity.

    Args:
        child_data: Dictionary containing child information
        entity_type: Type of entity (e.g., "tracker", "checkin", "checkout", "binary_sensor")

    Returns:
        Unique entity ID string

    """
    unique_id = child_data.get("unique_id", child_data.get(ATTR_CHILD_ID, "unknown"))
    return f"sodisys_{entity_type}_{unique_id}"
