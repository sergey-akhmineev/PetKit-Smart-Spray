# __init__.py
import asyncio
import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN, PLATFORMS
from .petkit_device import PetkitK3Device

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    devices = entry.data.get("devices", [])
    for device_conf in devices:
        device_id = device_conf["device_id"]
        name = device_conf["name"]
        mac = device_conf["mac"]
        secret = device_conf["secret"]
        petkit_device = PetkitK3Device(hass, name, mac, secret)
        hass.data[DOMAIN][device_id] = petkit_device
        hass.loop.create_task(petkit_device.heartbeat_loop())

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        for device in hass.data[DOMAIN].values():
            await device.shutdown()
        hass.data.pop(DOMAIN)
    return unload_ok