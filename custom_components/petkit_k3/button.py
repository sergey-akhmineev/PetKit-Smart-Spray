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
        PetkitK3LightOnButton(device)
    ]
    async_add_entities(buttons, True)

class PetkitK3SprayButton(ButtonEntity):
    """Кнопка для активации спрея на устройстве PetKit K3."""

    def __init__(self, device: PetkitK3Device):
        """Инициализация кнопки спрея."""
        self._device = device
        self._attr_name = "Кнопка Спрея PetKit"
        self._attr_unique_id = f"{device.address}_spray"

    async def async_press(self, **kwargs):
        """Обработка нажатия кнопки для активации спрея."""
        _LOGGER.debug("Нажата кнопка спрея")
        success = await self._device.spray()
        if success:
            _LOGGER.info("Спрей активирован успешно")
        else:
            _LOGGER.error("Не удалось активировать спрей")

class PetkitK3LightOnButton(ButtonEntity):
    """Кнопка для включения света на устройстве PetKit K3."""

    def __init__(self, device: PetkitK3Device):
        """Инициализация кнопки включения света."""
        self._device = device
        self._attr_name = "Кнопка Света PetKit"
        self._attr_unique_id = f"{device.address}_light_on"

    async def async_press(self, **kwargs):
        """Обработка нажатия кнопки для включения света."""
        _LOGGER.debug("Нажата кнопка включения света")
        success = await self._device.light_on()
        if success:
            _LOGGER.info("Свет включён успешно")
        else:
            _LOGGER.error("Не удалось включить свет")