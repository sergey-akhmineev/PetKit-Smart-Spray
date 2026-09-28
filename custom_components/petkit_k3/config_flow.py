# config_flow.py
import voluptuous as vol
import logging
import aiohttp
from homeassistant import config_entries
from homeassistant.const import CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from .const import (
    DOMAIN,
    DEFAULT_REGION,
    DEFAULT_TIMEZONE,
    CONF_REGION,
    CONF_TIMEZONE,
    CONF_IDLE_TIMEOUT,
    DEFAULT_IDLE_TIMEOUT,
    MAX_IDLE_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)
REGION_OPTIONS = ["FR", "US", "CN"]


class PetkitK3ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return PetkitK3OptionsFlow(config_entry)

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            username = user_input.get("username")
            password = user_input.get("password")
            region = user_input.get("region")
            timezone = user_input.get("timezone", DEFAULT_TIMEZONE)

            try:
                devices = await self._fetch_devices(username, password, region, timezone)
            except Exception as e:
                _LOGGER.exception("Ошибка при подключении к API")
                errors["base"] = "cannot_connect"
            else:
                if not devices:
                    errors["base"] = "no_devices"
                else:
                    self.context["api_data"] = {
                        "username": username,
                        "password": password,
                        "region": region,
                        "timezone": timezone,
                        "devices": devices,
                    }
                    return await self.async_step_select_devices()

        data_schema = vol.Schema({
            vol.Required("username"): str,
            vol.Required("password"): str,
            vol.Required("region", default=DEFAULT_REGION): vol.In(REGION_OPTIONS),
            vol.Required("timezone", default=DEFAULT_TIMEZONE): str,
        })
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    async def async_step_select_devices(self, user_input=None):
        api_data = self.context.get("api_data")
        if api_data is None:
            return await self.async_step_user()

        devices = api_data["devices"]
        device_options = {device["device_id"]: f"{device['name']} ({device['mac']})" for device in devices}
        if user_input is not None:
            selected_devices = user_input.get("devices")
            if not selected_devices:
                return self.async_show_form(
                    step_id="select_devices",
                    data_schema=vol.Schema({
                        vol.Required("devices"): cv.multi_select(device_options)
                    }),
                    errors={"base": "no_device_selected"}
                )
            selected = [device for device in devices if device["device_id"] in selected_devices]
            # Пароль от облака не сохраняем: для работы по Bluetooth нужны только MAC и секрет
            config_data = {
                CONF_USERNAME: api_data["username"],
                CONF_REGION: api_data["region"],
                CONF_TIMEZONE: api_data["timezone"],
                "devices": selected,
            }
            return self.async_create_entry(title="Petkit K3", data=config_data)

        data_schema = vol.Schema({
            vol.Required("devices"): cv.multi_select(device_options),
        })
        return self.async_show_form(step_id="select_devices", data_schema=data_schema)

    async def _fetch_devices(self, username, password, region, timezone):
        def import_petkit_client():
            from pypetkitapi.client import PetKitClient
            return PetKitClient

        PetKitClient = await self.hass.async_add_executor_job(import_petkit_client)
        session = aiohttp.ClientSession()
        devices_list = []
        try:
            client = PetKitClient(username=username, password=password, region=region, timezone=timezone,
                                  session=session)
            await client.get_devices_data()
            for device_id, device in client.petkit_entities.items():
                if getattr(device, "device_nfo", None) and getattr(device.device_nfo, "type", None) == 16:
                    device_dict = {
                        "device_id": str(device_id),
                        "name": device.name,
                        "mac": device.mac,
                        "secret": device.secret,
                    }
                    devices_list.append(device_dict)
        finally:
            await session.close()
        return devices_list


class PetkitK3OptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        idle_timeout = self._config_entry.options.get(CONF_IDLE_TIMEOUT, DEFAULT_IDLE_TIMEOUT)
        data_schema = vol.Schema({
            vol.Required(CONF_IDLE_TIMEOUT, default=idle_timeout): vol.All(
                vol.Coerce(int), vol.Range(min=0, max=MAX_IDLE_TIMEOUT)
            ),
        })
        return self.async_show_form(step_id="init", data_schema=data_schema)


CONFIG_FLOW = PetkitK3ConfigFlow