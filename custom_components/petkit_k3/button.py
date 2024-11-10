# button.py

import logging
from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN
from .device import PetkitK3Device

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up buttons for Petkit K3."""
    device: PetkitK3Device = hass.data[DOMAIN][entry.entry_id]
    buttons = [
        PetkitK3SprayButton(device)
    ]
    async_add_entities(buttons, True)


class PetkitK3SprayButton(ButtonEntity):
    """Representation of Petkit K3 Spray button."""

    def __init__(self, device: PetkitK3Device):
        """Initialize the spray button."""
        self._device = device
        self._attr_name = "Petkit K3 Spray"
        self._attr_unique_id = f"{device.address}_spray"

    async def async_press(self, **kwargs):
        """Handle the button press to activate spray."""
        _LOGGER.debug("Кнопка спрея нажата")
        success = await self._device.spray()
        if success:
            _LOGGER.info("Спрей успешно активирован")
        else:
            _LOGGER.error("Не удалось активировать спрей")