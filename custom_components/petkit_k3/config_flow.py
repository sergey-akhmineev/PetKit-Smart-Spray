"""Config flow for Petkit K3."""
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
    """Handle a config flow for Petkit K3."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_bluetooth(self, discovery_info: BluetoothServiceInfo) -> FlowResult:
        """Handle discovery of a Bluetooth device."""
        _LOGGER.debug("Обнаружено Bluetooth устройство: %s", discovery_info.address)

        # Проверка, что устройство является Petkit K3
        if not discovery_info.name or not discovery_info.name.startswith("Petkit"):
            _LOGGER.debug("Обнаруженное устройство не является Petkit")
            return self.async_abort(reason="not_petkit_k3")

        # Проверка, уже ли добавлено это конкретное устройство
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=discovery_info.name or DEFAULT_NAME,
            data={"address": discovery_info.address}
        )

    async def async_step_user(self, user_input: Dict[str, Any] = None) -> FlowResult:
        """Handle the initial step for manual configuration."""
        errors = {}

        if user_input is not None:
            # Установка уникального идентификатора на основе MAC-адреса
            await self.async_set_unique_id(user_input["address"])
            self._abort_if_unique_id_configured()

            # Здесь можно добавить дополнительную проверку, например, попытку подключения
            return self.async_create_entry(
                title=DEFAULT_NAME,
                data=user_input
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("address"): str,
            }),
            errors=errors
        )

    async def async_step_import(self, import_info: Dict[str, Any]) -> FlowResult:
        """Handle configuration import."""
        # Установка уникального идентификатора на основе MAC-адреса
        await self.async_set_unique_id(import_info["address"])
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=import_info.get("name", DEFAULT_NAME),
            data=import_info
        )