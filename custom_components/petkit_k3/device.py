# device.py

import logging
import asyncio
import random
from bleak import BleakClient, BleakError
from bleak.exc import BleakDeviceNotFoundError

from .const import CHARACTERISTIC_UUID, CMD_INIT, CMD_AUTH, CMD_SPRAY, CMD_LIGHT_ON

_LOGGER = logging.getLogger(__name__)

class PetkitK3Device:
    def __init__(self, address: str):
        """Инициализация устройства PetKit K3."""
        self.address = address
        self.client = None
        self.connected = False
        self._reconnect_task = None
        self._connect_lock = asyncio.Lock()
        self._is_reconnecting = False  # Флаг для предотвращения нескольких переподключений

    async def connect(self) -> bool:
        """Подключение к устройству."""
        async with self._connect_lock:
            if self.connected:
                _LOGGER.debug(f"Устройство {self.address} уже подключено.")
                return True

            if self._is_reconnecting:
                _LOGGER.debug(f"Переподключение к {self.address} уже в процессе.")
                return False  # Можно изменить на ожидание завершения переподключения

            try:
                self.client = BleakClient(self.address)
                await self.client.connect(timeout=20)
                self.connected = True
                _LOGGER.info(f"Подключено к {self.address}")
                await self.initialize()
                self.client.set_disconnected_callback(self.on_disconnected)
                return True
            except (BleakError, asyncio.TimeoutError) as e:
                _LOGGER.error(f"Не удалось подключиться: {e}")
                self.connected = False
                await self.start_reconnect()
                return False

    def on_disconnected(self, client):
        """Обработка отключения устройства."""
        _LOGGER.warning(f"Устройство {self.address} отключено")
        self.connected = False
        asyncio.create_task(self.start_reconnect())

    async def start_reconnect(self):
        """Запуск задачи переподключения."""
        if self._is_reconnecting:
            _LOGGER.debug("Переподключение уже запущено.")
            return
        self._reconnect_task = asyncio.create_task(self.reconnect())

    async def reconnect(self):
        """Попытка переподключения к устройству с ограничением числа попыток и экспоненциальным бэк-оффом."""
        self._is_reconnecting = True
        attempt = 0
        max_attempts = 5
        base_delay = 10  # Секунд

        try:
            while not self.connected and attempt < max_attempts:
                attempt += 1
                delay = base_delay * (2 ** (attempt - 1))  # Экспоненциальный бэк-офф
                _LOGGER.info(f"Попытка переподключения {attempt}/{max_attempts} к {self.address} через {delay} секунд")
                await asyncio.sleep(delay)

                try:
                    async with self._connect_lock:
                        if self.client:
                            try:
                                await self.client.disconnect()
                            except Exception:
                                pass

                        self.client = BleakClient(self.address)
                        await self.client.connect(timeout=20)
                        self.connected = True
                        _LOGGER.info(f"Переподключено к {self.address}")
                        await self.initialize()
                        self.client.set_disconnected_callback(self.on_disconnected)
                        break
                except BleakDeviceNotFoundError:
                    _LOGGER.error("Устройство не найдено при переподключении")
                except BleakError as e:
                    _LOGGER.error(f"Переподключение не удалось: {e}")
                except Exception as e:
                    _LOGGER.error(f"Неожиданная ошибка при переподключении: {e}")
        finally:
            if not self.connected:
                _LOGGER.error(f"Не удалось переподключиться к {self.address} после {max_attempts} попыток.")
            self._is_reconnecting = False

    async def disconnect(self):
        """Отключение от устройства."""
        if self._reconnect_task:
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                _LOGGER.debug("Задача переподключения отменена.")

        if self.client:
            try:
                await self.client.disconnect()
                _LOGGER.info(f"Отключено от {self.address}")
            except Exception as e:
                _LOGGER.error(f"Ошибка при отключении: {e}")
            finally:
                self.connected = False
                self.client = None

    async def send_command(self, command: str) -> bool:
        """Отправка команды устройству."""
        if not self.connected or not self.client:
            _LOGGER.error("Невозможно отправить команду, устройство не подключено")
            return False

        try:
            byte_command = bytes.fromhex(command)
            await self.client.write_gatt_char(CHARACTERISTIC_UUID, byte_command)
            _LOGGER.debug(f"Отправлена команда {command} в {self.address}")
            return True
        except Exception as e:
            _LOGGER.error(f"Не удалось отправить команду: {e}")
            self.connected = False
            await self.start_reconnect()
            return False

    async def initialize(self) -> bool:
        """Инициализация устройства путём отправки команд init и auth."""
        success_init = await self.send_command(CMD_INIT)
        await asyncio.sleep(0.5)
        success_auth = await self.send_command(CMD_AUTH)
        if success_init and success_auth:
            _LOGGER.info("Устройство успешно инициализировано")
            return True
        else:
            _LOGGER.error("Инициализация устройства не удалась")
            return False

    async def spray(self) -> bool:
        """Активация спрея."""
        if not self.connected:
            _LOGGER.warning("Невозможно активировать спрей, устройство не подключено")
            return False
        return await self.send_command(CMD_SPRAY)

    async def light_on(self) -> bool:
        """Включение света на 10 секунд."""
        if not self.connected:
            _LOGGER.warning("Невозможно включить свет, устройство не подключено")
            return False
        success = await self.send_command(CMD_LIGHT_ON)
        if success:
            _LOGGER.info("Свет включен на 10 секунд")
        return success