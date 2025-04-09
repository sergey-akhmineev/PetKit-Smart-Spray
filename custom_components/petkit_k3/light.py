# light.py
import logging
from homeassistant.components.light import LightEntity, ColorMode
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN, LIGHT_CMD

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    domain_data = hass.data[DOMAIN]
    entities = []
    for device_id, device in domain_data.items():
        entities.append(PetkitK3Light(device_id, device))
    async_add_entities(entities, update_before_add=True)

class PetkitK3Light(LightEntity):
    def __init__(self, device_id, device_controller):
        self._device_id = device_id
        self._controller = device_controller
        self._attr_name = f"{device_controller.name} Light"
        self._attr_is_on = device_controller.light_on
        self._attr_unique_id = f"{device_id}_light"
        self._attr_supported_color_modes = {ColorMode.ONOFF}
        self._attr_color_mode = ColorMode.ONOFF

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

    async def async_turn_on(self, **kwargs):
        resp = await self._controller.send_command(LIGHT_CMD)
        if resp == "00":
            self._controller.light_on = not self._controller.light_on
            self._attr_is_on = self._controller.light_on
        else:
            _LOGGER.error(f"Ошибка включения света для {self._controller.mac}")
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        await self.async_turn_on()

    async def async_update(self):
        self._attr_is_on = self._controller.light_on