# button.py
import logging
from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN, SPRAY_CMD

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    domain_data = hass.data[DOMAIN]
    entities = []
    for device_id, device in domain_data.items():
        entities.append(PetkitK3SprayButton(device_id, device))
    async_add_entities(entities, update_before_add=True)

class PetkitK3SprayButton(ButtonEntity):
    def __init__(self, device_id, device_controller):
        self._device_id = device_id
        self._controller = device_controller
        self._attr_name = f"{device_controller.name} Spray"
        self._attr_unique_id = f"{device_id}_spray"

    @property
    def available(self):
        return self._controller.available

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=self._controller.name,
            manufacturer="Petkit",
            model="K3"
        )

    async def async_press(self):
        resp = await self._controller.send_command(SPRAY_CMD)
        if resp != "00":
            _LOGGER.error(f"Ошибка запуска спрея для {self._controller.mac}")