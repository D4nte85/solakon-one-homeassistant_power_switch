"""Binary sensor platform for Solakon ONE integration."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Solakon ONE binary sensor entities."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    hub = hass.data[DOMAIN][config_entry.entry_id]["hub"]
    device_info = await hub.async_get_device_info()

    entities = [
        PowerStateBinarySensor(
            coordinator,
            config_entry,
            device_info,
        )
    ]

    async_add_entities(entities, True)


class PowerStateBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor for inverter power state."""

    def __init__(
        self,
        coordinator,
        config_entry: ConfigEntry,
        device_info: dict,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._device_info = device_info

        self._attr_unique_id = f"{config_entry.entry_id}_system_power_state"
        self.entity_id = "binary_sensor.solakon_one_power_state"
        self._attr_name = "Power State"
        self._attr_icon = "mdi:power"
        self._attr_device_class = "power"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._config_entry.entry_id)},
            name=self._config_entry.data.get("name", "Solakon ONE"),
            manufacturer=self._device_info.get("manufacturer", "Solakon"),
            model=self._device_info.get("model", "One"),
            sw_version=self._device_info.get("version"),
            serial_number=self._device_info.get("serial_number"),
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator.data and "system_power_state" in self.coordinator.data:
            value = self.coordinator.data["system_power_state"]
            self._attr_is_on = bool(value)
            _LOGGER.debug(f"Power state binary sensor updated: {self._attr_is_on}")
        else:
            self._attr_is_on = None

        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data is not None
