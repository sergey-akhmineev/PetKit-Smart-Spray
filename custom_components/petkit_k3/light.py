# light.py
from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import async_call_later

from .const import DOMAIN, LIGHT_CMD, LIGHT_ON_DURATION
from .entity import PetkitK3Entity
from .petkit_device import PetkitK3Error


async def async_setup_entry(hass, config_entry, async_add_entities):
    devices = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        PetkitK3Light(device_id, device) for device_id, device in devices.items()
    )


class PetkitK3Light(PetkitK3Entity, LightEntity):
    _attr_supported_color_modes = {ColorMode.ONOFF}
    _attr_color_mode = ColorMode.ONOFF

    def __init__(self, device_id, device_controller):
        super().__init__(device_id, device_controller)
        self._attr_name = f"{device_controller.name} Light"
        self._attr_unique_id = f"{device_id}_light"
        self._cancel_auto_off = None

    @property
    def is_on(self) -> bool:
        return self._controller.light_on

    async def _async_toggle(self) -> None:
        try:
            await self._controller.send_command(LIGHT_CMD)
        except PetkitK3Error as err:
            raise HomeAssistantError(f"Ошибка управления подсветкой: {err}") from err

    async def async_turn_on(self, **kwargs):
        if self.is_on:
            return
        await self._async_toggle()
        self._set_light(True)
        # Устройство само гасит подсветку — синхронизируем состояние в HA
        self._cancel_auto_off = async_call_later(
            self.hass, LIGHT_ON_DURATION, self._async_auto_off
        )

    async def async_turn_off(self, **kwargs):
        if not self.is_on:
            return
        # Команда подсветки работает как переключатель
        await self._async_toggle()
        self._set_light(False)

    @callback
    def _async_auto_off(self, _now) -> None:
        self._cancel_auto_off = None
        self._set_light(False)

    @callback
    def _set_light(self, state: bool) -> None:
        if not state and self._cancel_auto_off is not None:
            self._cancel_auto_off()
            self._cancel_auto_off = None
        self._controller.light_on = state
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        if self._cancel_auto_off is not None:
            self._cancel_auto_off()
            self._cancel_auto_off = None
