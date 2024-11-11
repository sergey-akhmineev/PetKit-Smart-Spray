# config_flow.py

import logging
from typing import Any, Dict

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.bluetooth import BluetoothServiceInfo
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, DEFAULT_NAME

_LOGGER = logging.getLogger(__name__)

class PetkitK3ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Обработка процесса настройки для Petkit K3."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_bluetooth(self, discovery_info: BluetoothServiceInfo) -> FlowResult:
        """Обработка обнаружения устройства по Bluetooth."""
        _LOGGER.debug("Обнаружено Bluetooth устройство: %s", discovery_info.address)

        # Проверка, что устройство является Petkit K3
        if not discovery_info.name or not discovery_info.name.startswith("Petkit"):
            _LOGGER.debug("Обнаруженное устройство не является Petkit K3")
            return self.async_abort(reason="not_petkit_k3")

        # Проверка, не настроено ли уже устройство
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        # Дополнительно можно проверить доступность устройства

        return self.async_create_entry(
            title=discovery_info.name or DEFAULT_NAME,
            data={"address": discovery_info.address}
        )

    async def async_step_user(self, user_input: Dict[str, Any] = None) -> FlowResult:
        """Обработка пользовательской инициации настройки."""
        errors = {}

        if user_input is not None:
            address = user_input.get("address")
            if address:
                # Установка уникального идентификатора для предотвращения дублирования
                await self.async_set_unique_id(address)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=DEFAULT_NAME,
                    data=user_input
                )
            else:
                errors["address"] = "invalid_address"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("address"): str,
            }),
            errors=errors
        )

    async def async_step_import(self, import_info: Dict[str, Any]) -> FlowResult:
        """Обработка импорта конфигурации."""
        address = import_info.get("address")
        if not address:
            return self.async_abort(reason="invalid_address")

        # Установка уникального идентификатора
        await self.async_set_unique_id(address)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=import_info.get("name", DEFAULT_NAME),
            data=import_info
        )