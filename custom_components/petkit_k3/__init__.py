# __init__.py
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_IDLE_TIMEOUT, DEFAULT_IDLE_TIMEOUT, DOMAIN, PLATFORMS
from .petkit_device import PetkitK3Device

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    idle_timeout = entry.options.get(CONF_IDLE_TIMEOUT, DEFAULT_IDLE_TIMEOUT)

    devices: dict[str, PetkitK3Device] = {}
    for device_conf in entry.data.get("devices", []):
        try:
            petkit_device = PetkitK3Device(
                hass,
                device_conf["name"],
                device_conf["mac"],
                device_conf["secret"],
                idle_timeout,
            )
        except ValueError as err:
            _LOGGER.error("Пропускаю устройство %s: %s", device_conf.get("name"), err)
            continue
        # Только пассивное отслеживание рекламы — к устройству не подключаемся
        petkit_device.async_start()
        devices[device_conf["device_id"]] = petkit_device

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = devices
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        devices = hass.data[DOMAIN].pop(entry.entry_id)
        for device in devices.values():
            await device.shutdown()
    return unload_ok
