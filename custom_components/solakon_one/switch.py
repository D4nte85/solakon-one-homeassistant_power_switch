"""Switch platform for Solakon ONE integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
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
    """Set up Solakon ONE switch entities."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    hub = hass.data[DOMAIN][config_entry.entry_id]["hub"]
    device_info = await hub.async_get_device_info()

    entities = [
        PowerSwitch(
            coordinator,
            hub,
            config_entry,
            device_info,
        )
    ]

    async_add_entities(entities, True)


class PowerSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a Solakon ONE Power Switch."""

    def __init__(
        self,
        coordinator,
        hub,
        config_entry: ConfigEntry,
        device_info: dict,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._hub = hub
        self._config_entry = config_entry
        self._device_info = device_info

        self._attr_unique_id = f"{config_entry.entry_id}_power_switch"
        self.entity_id = "switch.solakon_one_power"
        self._attr_name = "Power"
        self._attr_icon = "mdi:power"

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
            _LOGGER.debug(f"Power switch state updated: {self._attr_is_on}")
        else:
            self._attr_is_on = None

        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the inverter on."""
        _LOGGER.info("Turning inverter ON")
        success = await self._hub.async_write_register(49077, 1)
        if success:
            _LOGGER.info("Successfully sent power ON command")
            self._attr_is_on = True
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to send power ON command")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the inverter off."""
        _LOGGER.info("Turning inverter OFF")
        success = await self._hub.async_write_register(49078, 1)
        if success:
            _LOGGER.info("Successfully sent power OFF command")
            self._attr_is_on = False
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to send power OFF command")

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data is not None
