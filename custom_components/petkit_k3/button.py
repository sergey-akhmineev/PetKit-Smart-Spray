# button.py

import logging
from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN
from .device import PetkitK3Device

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Настройка кнопок для PetKit K3."""
    device: PetkitK3Device = hass.data[DOMAIN][entry.entry_id]
    buttons = [
        PetkitK3SprayButton(device),
        PetkitK3LightButton(device)
    ]
    async_add_entities(buttons, True)


class PetkitK3SprayButton(ButtonEntity):
    """Представление кнопки спрея PetKit K3."""

    def __init__(self, device: PetkitK3Device):
        """Инициализация кнопки спрея."""
        self._device = device
        self._attr_name = "PetKit Spray Button"
        self._attr_unique_id = f"{device.address}_spray"

    async def async_press(self, **kwargs):
        """Обработка нажатия кнопки для активации спрея."""
        _LOGGER.debug("Кнопка спрея нажата")
        success = await self._device.spray()
        if success:
            _LOGGER.info("Спрей успешно активирован")
        else:
            _LOGGER.error("Не удалось активировать спрей")


class PetkitK3LightButton(ButtonEntity):
    """Представление кнопки света PetKit K3."""

    def __init__(self, device: PetkitK3Device):
        """Инициализация кнопки света."""
        self._device = device
        self._attr_name = "PetKit Light Button"
        self._attr_unique_id = f"{device.address}_light_button"

    async def async_press(self, **kwargs):
        """Обработка нажатия кнопки для включения света."""
        _LOGGER.debug("Кнопка света нажата")
        success = await self._device.light_on()
        if success:
            _LOGGER.info("Свет успешно включен")
        else:
            _LOGGER.error("Не удалось включить свет")