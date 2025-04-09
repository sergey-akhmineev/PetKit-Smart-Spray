# petkit_device.py
import asyncio
import logging

from bleak import BleakClient
from bleak.exc import BleakError

# ОБРАТИТЕ ВНИМАНИЕ: добавляем импорт функции ниже,
# чтобы получать Bluetooth-устройство через Home Assistant
from homeassistant.components.bluetooth import async_ble_device_from_address

from .const import (
    CHAR_UUID,
    INIT_CMD,
    AUTH_CMD_PREFIX,
    AUTH_CMD_SUFFIX,
    SCAN_INTERVAL,
    SPRAY_CMD,
    LIGHT_CMD,
)

_LOGGER = logging.getLogger(__name__)


class PetkitK3Device:
    def __init__(self, hass, name: str, mac: str, secret: str):
        self.hass = hass
        self.name = name
        self.mac = self.format_mac(mac)
        self.secret = secret
        self.client = None
        self.available = False
        self.light_on = False
        self._shutdown = False
        self.lock = asyncio.Lock()  # Блокировка для последовательного выполнения команд
        self._connect_lock = asyncio.Lock()  # Блокировка для подключения
        self._connect_attempts = 0  # Счетчик попыток подключения
        self._max_connect_attempts = 5  # Максимальное количество попыток перед задержкой
        self._reconnect_delay = 10  # Начальная задержка в секундах

    def format_mac(self, mac_str: str) -> str:
        mac_str = mac_str.replace(":", "").upper()
        if len(mac_str) != 12:
            raise ValueError("Неверный формат MAC-адреса")
        return ":".join(mac_str[i:i + 2] for i in range(0, 12, 2))

    def _handle_disconnect(self, client):
        self.available = False
        _LOGGER.warning(f"Устройство {self.mac} отключилось")
        # Автопереподключение
        asyncio.create_task(self.async_connect())

    async def async_connect(self) -> bool:
        async with self._connect_lock:
            if self._connect_attempts >= self._max_connect_attempts:
                _LOGGER.warning(
                    f"Достигнуто максимальное количество попыток для {self.mac}, ожидание {self._reconnect_delay} сек"
                )
                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(
                    300,
                    self._reconnect_delay * 2
                )  # Увеличиваем задержку экспоненциально до 5 минут
                self._connect_attempts = 0

            # Если уже подключено, сбрасываем счетчики
            if self.client and self.client.is_connected:
                self._connect_attempts = 0
                self._reconnect_delay = 10
                return True

            # Попробуем получить Bluetooth-устройство через Home Assistant
            ble_device = async_ble_device_from_address(self.hass, self.mac, connectable=True)
            if not ble_device:
                _LOGGER.error(
                    f"Не удалось найти устройство Bluetooth для адреса {self.mac}. Возможно, оно вне зоны видимости."
                )
                self.available = False
                return False

            try:
                # Если ранее был создан клиент, сначала пробуем отключить его
                if self.client:
                    try:
                        await self.client.disconnect()
                    except Exception as e:
                        _LOGGER.debug(f"Ошибка отключения перед повторным подключением: {e}")

                self.client = BleakClient(
                    ble_device,
                    disconnected_callback=self._handle_disconnect
                )
                await self.client.connect(timeout=20.0)
                _LOGGER.info(f"Установлено подключение к {self.mac}")
                self.available = True

                # Обновление состояния сущностей (пример для кнопки спрея)
                self.hass.async_create_task(
                    self.hass.services.async_call(
                        "homeassistant",
                        "update_entity",
                        {"entity_id": f"button.{self.name.lower()}_spray"}
                    )
                )

                self._connect_attempts = 0
                self._reconnect_delay = 10
                return True
            except BleakError as e:
                _LOGGER.error(f"Ошибка подключения к {self.mac}: {e}")
                self.available = False
                self.client = None
                self._connect_attempts += 1
                return False

    async def _write_command(self, command_hex: str):
        if not self.client or not self.client.is_connected:
            connected = await self.async_connect()
            if not connected:
                return None
        try:
            data = bytes.fromhex(command_hex)
            await self.client.write_gatt_char(CHAR_UUID, data)
            _LOGGER.debug(f"Команда {command_hex} отправлена")
            await asyncio.sleep(0.5)
            try:
                response = await self.client.read_gatt_char(CHAR_UUID)
                resp_hex = response.hex()
                _LOGGER.debug(f"Ответ: {resp_hex}")
                return resp_hex
            except Exception:
                _LOGGER.debug("Ответ не получен")
                return None
        except Exception as e:
            _LOGGER.error(f"Ошибка отправки команды {command_hex} к {self.mac}: {e}")
            if self.client and self.client.is_connected:
                try:
                    await self.client.disconnect()
                except Exception as e2:
                    _LOGGER.debug(f"Ошибка при отключении: {e2}")
            self.client = None
            return None

    async def send_command(self, command: str):
        async with self.lock:
            # Инициализация и аутентификация перед выполнением основной команды
            await self._write_command(INIT_CMD)
            auth_command = AUTH_CMD_PREFIX + self.secret + AUTH_CMD_SUFFIX
            auth_resp = await self._write_command(auth_command)
            if auth_resp != "00":
                _LOGGER.warning(f"Неверный ответ аутентификации для {self.mac}: {auth_resp}")
                self.available = False
                return None
            resp = await self._write_command(command)
            if resp == "00":
                self.available = True
            else:
                self.available = False
            return resp

    async def heartbeat_loop(self):
        while not self._shutdown:
            try:
                # Вместо немедленного подключения добавляем проверку
                if not self.client or not self.client.is_connected:
                    # Пытаемся подключиться с ограничением
                    if self._connect_attempts < self._max_connect_attempts:
                        await self.async_connect()
                    else:
                        await asyncio.sleep(self._reconnect_delay)

                async with self.lock:
                    await self._write_command(INIT_CMD)
                    auth_command = AUTH_CMD_PREFIX + self.secret + AUTH_CMD_SUFFIX
                    auth_resp = await self._write_command(auth_command)
                    if auth_resp == "00":
                        _LOGGER.debug(f"Heartbeat успешен для {self.mac}")
                        self.available = True
                    else:
                        _LOGGER.debug(f"Heartbeat неуспешен для {self.mac}, пробую переподключиться")
                        self.available = False
                        await self.async_connect()
            except Exception as e:
                _LOGGER.exception(f"Ошибка в heartbeat_loop: {e}")

            await asyncio.sleep(SCAN_INTERVAL)

    async def shutdown(self):
        self._shutdown = True
        if self.client and self.client.is_connected:
            await self.client.disconnect()