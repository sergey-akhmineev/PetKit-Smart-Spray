"""Petkit K3 device control."""
import logging
import asyncio
import random
from bleak import BleakClient, BleakError
from bleak.exc import BleakDeviceNotFoundError

from .const import CHARACTERISTIC_UUID, CMD_INIT, CMD_AUTH, CMD_SPRAY, CMD_LIGHT_ON, CMD_LIGHT_OFF

_LOGGER = logging.getLogger(__name__)


class PetkitK3Device:
    def __init__(self, address):
        """Initialize the device."""
        self.address = address
        self.client = None
        self.connected = False
        self._reconnect_task = None
        self._connect_lock = asyncio.Lock()

    async def connect(self):
        """Connect to the device."""
        async with self._connect_lock:
            if self.connected:
                return True

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
                self.start_reconnect()
                return False

    def on_disconnected(self, client):
        """Handle device disconnection."""
        _LOGGER.warning(f"Устройство {self.address} отключено")
        self.connected = False
        self.start_reconnect()

    def start_reconnect(self):
        """Start the reconnection task."""
        if not self._reconnect_task or self._reconnect_task.done():
            self._reconnect_task = asyncio.create_task(self.reconnect())

    async def reconnect(self):
        """Attempt to reconnect to the device."""
        while not self.connected:
            try:
                _LOGGER.info(f"Попытка переподключения к {self.address}")
                await asyncio.sleep(random.uniform(10, 15))  # Случайная задержка

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
                _LOGGER.error("Устройство не найдено")
                await asyncio.sleep(15)
            except BleakError as e:
                _LOGGER.error(f"Переподключение не удалось: {e}")
                await asyncio.sleep(15)
            except asyncio.CancelledError:
                _LOGGER.warning("Задача переподключения была отменена")
                break
            except Exception as e:
                _LOGGER.error(f"Неожиданная ошибка при переподключении: {e}")
                await asyncio.sleep(15)

    async def disconnect(self):
        """Disconnect from the device."""
        if self._reconnect_task:
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass

        if self.client:
            try:
                await self.client.disconnect()
            except Exception as e:
                _LOGGER.error(f"Ошибка при отключении: {e}")
            finally:
                self.connected = False
                self.client = None

    async def send_command(self, command):
        """Send command to device."""
        if not self.connected or not self.client:
            _LOGGER.error("Устройство не подключено")
            return False

        try:
            byte_command = bytes.fromhex(command)
            await self.client.write_gatt_char(CHARACTERISTIC_UUID, byte_command)
            return True
        except Exception as e:
            _LOGGER.error(f"Не удалось отправить команду: {e}")
            self.connected = False
            self.start_reconnect()
            return False

    async def initialize(self):
        """Initialize the device."""
        await self.send_command(CMD_INIT)
        await asyncio.sleep(0.5)
        await self.send_command(CMD_AUTH)

    async def spray(self):
        """Activate spray."""
        if not self.connected:
            _LOGGER.warning("Невозможно активировать спрей, устройство не подключено")
            return False
        return await self.send_command(CMD_SPRAY)

    async def light_on(self):
        """Turn on light."""
        if not self.connected:
            _LOGGER.warning("Невозможно включить свет, устройство не подключено")
            return False
        return await self.send_command(CMD_LIGHT_ON)

    async def light_off(self):
        """Turn off light."""
        if not self.connected:
            _LOGGER.warning("Невозможно выключить свет, устройство не подключено")
            return False
        return await self.send_command(CMD_LIGHT_OFF)