# entity.py
from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH

from .const import DOMAIN
from .petkit_device import PetkitK3Device


class PetkitK3Entity(Entity):
    """Общая часть сущностей K3: состояние приходит от устройства, без опроса."""

    _attr_should_poll = False

    def __init__(self, device_id: str, device_controller: PetkitK3Device) -> None:
        self._device_id = device_id
        self._controller = device_controller
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            connections={(CONNECTION_BLUETOOTH, device_controller.mac)},
            name=device_controller.name,
            manufacturer="Petkit",
            model="K3",
        )

    @property
    def available(self) -> bool:
        return self._controller.available

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            self._controller.async_add_listener(self.async_write_ha_state)
        )
