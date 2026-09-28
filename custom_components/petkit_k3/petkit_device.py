# petkit_device.py
"""BLE-клиент Petkit K3.

Устройство питается от батареи, поэтому соединение НЕ держится постоянно:
пока K3 подключён, он обязан отвечать на каждое событие соединения
(десятки раз в секунду) и не может уйти в сон. Вместо этого:

* доступность определяется пассивно — по рекламным пакетам (advertisements),
  которые K3 и так рассылает; устройство при этом ничего не тратит;
* соединение открывается только для отправки команды, аутентификация
  выполняется один раз на соединение;
* после простоя ``idle_timeout`` секунд соединение закрывается;
* после разрыва автоматического переподключения нет — следующее
  подключение произойдёт только при следующей команде.
"""
from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable

from bleak.exc import BleakError
from bleak_retry_connector import (
    BleakClientWithServiceCache,
    establish_connection,
)

from homeassistant.components import bluetooth
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback

from .const import (
    AUTH_CMD_PREFIX,
    AUTH_CMD_SUFFIX,
    CHAR_UUID,
    CONNECT_MAX_ATTEMPTS,
    DEFAULT_IDLE_TIMEOUT,
    INIT_CMD,
    RESPONSE_DELAY,
    RESPONSE_OK,
)

_LOGGER = logging.getLogger(__name__)

BLE_EXCEPTIONS = (BleakError, asyncio.TimeoutError, EOFError, BrokenPipeError)


class PetkitK3Error(Exception):
    """Команду не удалось выполнить."""


class PetkitK3Device:
    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        mac: str,
        secret: str,
        idle_timeout: int = DEFAULT_IDLE_TIMEOUT,
    ) -> None:
        self.hass = hass
        self.name = name
        self.mac = self.format_mac(mac)
        self.secret = secret
        self.idle_timeout = idle_timeout
        self.light_on = False

        self._client: BleakClientWithServiceCache | None = None
        self._authenticated = False
        self._present = False
        self._shutdown = False
        self._lock = asyncio.Lock()  # команды и подключение выполняются последовательно
        self._disconnect_timer: asyncio.TimerHandle | None = None
        self._listeners: set[CALLBACK_TYPE] = set()
        self._unsubs: list[CALLBACK_TYPE] = []

    @staticmethod
    def format_mac(mac_str: str) -> str:
        mac_str = mac_str.replace(":", "").upper()
        if len(mac_str) != 12:
            raise ValueError("Неверный формат MAC-адреса")
        return ":".join(mac_str[i:i + 2] for i in range(0, 12, 2))

    @property
    def is_connected(self) -> bool:
        return self._client is not None and self._client.is_connected

    @property
    def available(self) -> bool:
        # Пока K3 подключён, он не рассылает рекламу — поэтому учитываем и соединение
        return self._present or self.is_connected

    # ---------- Пассивное отслеживание доступности ----------

    @callback
    def async_start(self) -> None:
        """Подписаться на рекламные пакеты устройства (без подключения к нему)."""
        self._present = bluetooth.async_address_present(
            self.hass, self.mac, connectable=True
        )
        self._unsubs.append(
            bluetooth.async_register_callback(
                self.hass,
                self._async_on_advertisement,
                bluetooth.BluetoothCallbackMatcher(address=self.mac, connectable=True),
                bluetooth.BluetoothScanningMode.PASSIVE,
            )
        )
        self._unsubs.append(
            bluetooth.async_track_unavailable(
                self.hass, self._async_on_unavailable, self.mac, connectable=True
            )
        )

    @callback
    def async_add_listener(self, update_callback: CALLBACK_TYPE) -> Callable[[], None]:
        self._listeners.add(update_callback)
        return lambda: self._listeners.discard(update_callback)

    @callback
    def _async_notify(self) -> None:
        for update_callback in list(self._listeners):
            update_callback()

    @callback
    def _async_on_advertisement(
        self,
        service_info: bluetooth.BluetoothServiceInfoBleak,
        change: bluetooth.BluetoothChange,
    ) -> None:
        if not self._present:
            _LOGGER.debug("%s снова в зоне видимости", self.mac)
            self._present = True
            self._async_notify()

    @callback
    def _async_on_unavailable(self, service_info: bluetooth.BluetoothServiceInfoBleak) -> None:
        if self._present:
            _LOGGER.debug("%s пропал из эфира", self.mac)
            self._present = False
            self._async_notify()

    # ---------- Соединение ----------

    def _handle_disconnect(self, client) -> None:
        if self._client is not None and self._client.is_connected:
            return  # запоздавший колбэк от предыдущего соединения
        _LOGGER.debug("Устройство %s отключилось", self.mac)
        self._client = None
        self._authenticated = False
        self._cancel_disconnect_timer()
        # Без автопереподключения: это и есть основная экономия батареи
        self._async_notify()

    async def _write(self, client: BleakClientWithServiceCache, command_hex: str) -> str | None:
        """Отправить команду и прочитать ответ. Ошибки записи пробрасываются."""
        await client.write_gatt_char(CHAR_UUID, bytes.fromhex(command_hex))
        _LOGGER.debug("%s: команда %s отправлена", self.mac, command_hex)
        await asyncio.sleep(RESPONSE_DELAY)
        try:
            response = await client.read_gatt_char(CHAR_UUID)
        except BLE_EXCEPTIONS as err:
            _LOGGER.debug("%s: ответ не получен: %s", self.mac, err)
            return None
        resp_hex = response.hex()
        _LOGGER.debug("%s: ответ %s", self.mac, resp_hex)
        return resp_hex

    async def _ensure_session(self) -> BleakClientWithServiceCache:
        """Подключиться (если нужно) и пройти аутентификацию один раз на соединение."""
        client = self._client
        if not self.is_connected:
            ble_device = bluetooth.async_ble_device_from_address(
                self.hass, self.mac, connectable=True
            )
            if ble_device is None:
                raise PetkitK3Error(
                    f"{self.name} ({self.mac}) вне зоны видимости Bluetooth"
                )
            self._authenticated = False
            client = self._client = await establish_connection(
                BleakClientWithServiceCache,
                ble_device,
                self.name,
                disconnected_callback=self._handle_disconnect,
                max_attempts=CONNECT_MAX_ATTEMPTS,
                ble_device_callback=lambda: bluetooth.async_ble_device_from_address(
                    self.hass, self.mac, connectable=True
                ) or ble_device,
            )
            _LOGGER.debug("Установлено подключение к %s", self.mac)
            self._async_notify()

        if not self._authenticated:
            await self._write(client, INIT_CMD)
            auth_resp = await self._write(
                client, AUTH_CMD_PREFIX + self.secret + AUTH_CMD_SUFFIX
            )
            if auth_resp != RESPONSE_OK:
                raise PetkitK3Error(
                    f"Неверный ответ аутентификации от {self.mac}: {auth_resp}"
                )
            self._authenticated = True
        return client

    async def _disconnect(self) -> None:
        self._cancel_disconnect_timer()
        client, self._client = self._client, None
        self._authenticated = False
        if client is not None:
            try:
                await client.disconnect()
            except BLE_EXCEPTIONS as err:
                _LOGGER.debug("%s: ошибка при отключении: %s", self.mac, err)
            self._async_notify()

    # ---------- Отключение по простою ----------

    def _cancel_disconnect_timer(self) -> None:
        if self._disconnect_timer is not None:
            self._disconnect_timer.cancel()
            self._disconnect_timer = None

    def _schedule_disconnect(self) -> None:
        self._cancel_disconnect_timer()
        self._disconnect_timer = self.hass.loop.call_later(
            self.idle_timeout, self._on_idle_timeout
        )

    @callback
    def _on_idle_timeout(self) -> None:
        self._disconnect_timer = None
        self.hass.async_create_background_task(
            self._async_idle_disconnect(), f"petkit_k3 idle disconnect {self.mac}"
        )

    async def _async_idle_disconnect(self) -> None:
        async with self._lock:
            # Пока ждали блокировку, новая команда могла перезапустить таймер
            if self._disconnect_timer is not None:
                return
            _LOGGER.debug("%s: простой %s с, отключаюсь", self.mac, self.idle_timeout)
            await self._disconnect()

    # ---------- Публичный API ----------

    async def send_command(self, command: str) -> None:
        """Выполнить команду; при ошибке — PetkitK3Error."""
        if self._shutdown:
            raise PetkitK3Error("Интеграция выгружается")
        async with self._lock:
            self._cancel_disconnect_timer()
            try:
                client = await self._ensure_session()
                resp = await self._write(client, command)
            except PetkitK3Error:
                await self._disconnect()
                raise
            except BLE_EXCEPTIONS as err:
                await self._disconnect()
                raise PetkitK3Error(f"Ошибка связи с {self.mac}: {err}") from err

            if resp != RESPONSE_OK:
                # Начинаем следующую команду с чистой сессии
                await self._disconnect()
                raise PetkitK3Error(f"Неверный ответ от {self.mac} на {command}: {resp}")

            if self.idle_timeout > 0:
                self._schedule_disconnect()
            else:
                await self._disconnect()

    async def shutdown(self) -> None:
        self._shutdown = True
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        self._listeners.clear()
        await self._disconnect()
