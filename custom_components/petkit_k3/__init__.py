# __init__.py

import asyncio
import logging
from bleak import BleakScanner
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components import bluetooth

from .const import DOMAIN
from .device import PetkitK3Device

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["button"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Настройка PetKit K3 по конфигурационной записи."""
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
        """Остановка устройства PetKit."""
        await device.disconnect()

    entry.async_on_unload(
        hass.bus.async_listen_once("homeassistant_stop", stop_petkit)
    )

    # Запуск фоновой задачи для поиска новых устройств
    hass.async_create_task(scan_for_devices(hass))

    return True


async def scan_for_devices(hass: HomeAssistant):
    """Фоновая задача для постоянного сканирования устройств."""
    while True:
        try:
            devices = await BleakScanner.discover(timeout=15.0)
            for device in devices:
                if device.name and device.name.startswith("Petkit"):
                    _LOGGER.info(f"Обнаружено устройство: {device.name} ({device.address})")
                    # Проверка, уже добавлено ли устройство
                    if not any(
                        entry.data["address"] == device.address
                        for entry in hass.config_entries.async_entries(DOMAIN)
                    ):
                        # Запуск мастера настройки для подключения
                        hass.async_create_task(
                            hass.config_entries.flow.async_init(
                                DOMAIN,
                                context={"source": "bluetooth"},
                                data={"address": device.address, "name": device.name},
                            )
                        )
        except Exception as e:
            _LOGGER.error(f"Ошибка при сканировании устройств: {e}")

        await asyncio.sleep(15)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Выгрузка конфигурационной записи."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        device = hass.data[DOMAIN].pop(entry.entry_id)
        await device.disconnect()

    return unload_ok