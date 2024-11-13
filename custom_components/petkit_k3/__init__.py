# __init.py__

"""The Petkit K3 integration."""
import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components import bluetooth

from .const import DOMAIN
from .device import PetkitK3Device

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["switch", "button"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Petkit K3 from a config entry."""
    device = PetkitK3Device(entry.data["address"])

    # Делаем несколько попыток подключения
    for attempt in range(3):
        try:
            connect_success = await device.connect()
            if connect_success:
                break
        except Exception as e:
            _LOGGER.error(f"Попытка подключения {attempt + 1} не удалась: {e}")
            await asyncio.sleep(2)
    else:
        _LOGGER.error("Не удалось подключиться к устройству после нескольких попыток")
        return False

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = device

    # Подключаем платформы
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Подписаться на сигнал остановки Home Assistant для отключения устройства
    async def stop_petkit(event):
        """Stop Petkit device."""
        await device.disconnect()

    entry.async_on_unload(
        hass.bus.async_listen_once("homeassistant_stop", stop_petkit)
    )

    # Запуск фоновой задачи для поиска устройств
    hass.loop.create_task(scan_for_devices(hass))

    return True


async def scan_for_devices(hass: HomeAssistant):
    """Фоновая задача для постоянного сканирования устройств."""
    while True:
        try:
            scanner = bluetooth.async_get_scanner(hass)
            if scanner is None:
                _LOGGER.error("Bluetooth сканер недоступен")
                await asyncio.sleep(30)
                continue

            discovered_devices = await scanner.discover(timeout=10.0)

            for device in discovered_devices:
                if device.name and device.name.startswith("Petkit"):
                    _LOGGER.info(f"Обнаружено устройство: {device.name} ({device.address})")
                    # Проверка, уже добавлено ли устройство
                    if not any(
                            entry.data.get("address") == device.address
                            for entry in hass.config_entries.async_entries(DOMAIN)
                    ):
                        # Запуск мастера настройки для подключения
                        hass.async_create_task(
                            hass.config_entries.flow.async_init(
                                DOMAIN,
                                context={"source": "bluetooth"},
                                data={"address": device.address},
                            )
                        )
        except Exception as e:
            _LOGGER.error(f"Ошибка при сканировании устройств: {e}")

        await asyncio.sleep(15)  # Интервал между сканированием


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        device = hass.data[DOMAIN].pop(entry.entry_id)
        await device.disconnect()

    return unload_ok