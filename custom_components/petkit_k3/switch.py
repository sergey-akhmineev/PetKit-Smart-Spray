# switch.py

import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN
from .device import PetkitK3Device

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up switches for Petkit K3."""
    device: PetkitK3Device = hass.data[DOMAIN][entry.entry_id]
    switches = [
        PetkitK3Light(device),
        PetkitK3Spray(device)
    ]
    async_add_entities(switches, True)


class PetkitK3Spray(SwitchEntity):
    """Representation of Petkit K3 Spray switch."""

    def __init__(self, device: PetkitK3Device):
        """Initialize the spray switch."""
        self._device = device
        self._attr_name = "Переключатель Спрея PetKit"
        self._attr_unique_id = f"{device.address}_spray"
        self._attr_is_on = False

    async def async_turn_on(self, **kwargs):
        """Handle the button press to on spray."""
        _LOGGER.debug("Спрей включен")
        success = await self._device.spray_on()
        if success:
            self._attr_is_on = True
            self.async_write_ha_state()
        else:
            _LOGGER.error("Не удалось активировать спрей")

    async def async_turn_off(self, **kwargs):
        """Handle the button press to off spray."""
        _LOGGER.debug("Спрей выключен")
        success = await self._device.spray_off()
        if success:
            self._attr_is_on = True
            self.async_write_ha_state()
        else:
            _LOGGER.error("Не удалось активировать спрей")


class PetkitK3Light(SwitchEntity):
    """Representation of Petkit K3 Light switch."""

    def __init__(self, device: PetkitK3Device):
        """Initialize the light switch."""
        self._device = device
        self._attr_name = "Переключатель Света PetKit"
        self._attr_unique_id = f"{device.address}_light"
        self._attr_is_on = False

    async def async_turn_on(self, **kwargs):
        """Turn on the light."""
        _LOGGER.debug("Включение света")
        success = await self._device.light_on()
        if success:
            self._attr_is_on = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn off the light."""
        _LOGGER.debug("Выключение света")
        success = await self._device.light_off()
        if success:
            self._attr_is_on = False
            self.async_write_ha_state()