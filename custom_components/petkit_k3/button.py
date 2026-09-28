# button.py
from homeassistant.components.button import ButtonEntity
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, SPRAY_CMD
from .entity import PetkitK3Entity
from .petkit_device import PetkitK3Error


async def async_setup_entry(hass, config_entry, async_add_entities):
    devices = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        PetkitK3SprayButton(device_id, device) for device_id, device in devices.items()
    )


class PetkitK3SprayButton(PetkitK3Entity, ButtonEntity):
    def __init__(self, device_id, device_controller):
        super().__init__(device_id, device_controller)
        self._attr_name = f"{device_controller.name} Spray"
        self._attr_unique_id = f"{device_id}_spray"

    async def async_press(self):
        try:
            await self._controller.send_command(SPRAY_CMD)
        except PetkitK3Error as err:
            raise HomeAssistantError(f"Ошибка запуска спрея: {err}") from err
