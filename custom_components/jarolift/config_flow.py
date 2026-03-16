"""Config flow for Jarolift integration."""
import asyncio
import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_NUM_CHANNELS,
    CONF_NUM_GROUPS,
    CONF_CHANNEL_NAMES,
    CONF_GROUP_NAMES,
    DEFAULT_NUM_CHANNELS,
    DEFAULT_NUM_GROUPS,
)
from .websocket_client import JaroliftWebSocket

_LOGGER = logging.getLogger(__name__)


class JaroliftConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Jarolift."""

    VERSION = 1

    def __init__(self) -> None:
        self._host: str = ""
        self._num_channels: int = DEFAULT_NUM_CHANNELS
        self._num_groups: int = DEFAULT_NUM_GROUPS

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Step 1: Host + channel/group count."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._host = user_input[CONF_HOST]
            self._num_channels = user_input[CONF_NUM_CHANNELS]
            self._num_groups = user_input[CONF_NUM_GROUPS]

            # Test connection
            ws = JaroliftWebSocket(self._host, lambda _: None)
            ok = await ws.async_test_connection()
            if not ok:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(self._host)
                self._abort_if_unique_id_configured()
                return await self.async_step_channel_names()

        schema = vol.Schema({
            vol.Required(CONF_HOST, default=self._host): str,
            vol.Required(CONF_NUM_CHANNELS, default=DEFAULT_NUM_CHANNELS): vol.All(int, vol.Range(min=1, max=16)),
            vol.Required(CONF_NUM_GROUPS, default=DEFAULT_NUM_GROUPS): vol.All(int, vol.Range(min=0, max=6)),
        })

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_channel_names(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Step 2: Name each channel."""
        if user_input is not None:
            channel_names = {str(i): user_input.get(f"channel_{i}", f"Kanal {i + 1}") for i in range(self._num_channels)}

            if self._num_groups > 0:
                self._channel_names = channel_names
                return await self.async_step_group_names()

            return self.async_create_entry(
                title=f"Jarolift ({self._host})",
                data={
                    CONF_HOST: self._host,
                    CONF_NUM_CHANNELS: self._num_channels,
                    CONF_NUM_GROUPS: self._num_groups,
                    CONF_CHANNEL_NAMES: channel_names,
                    CONF_GROUP_NAMES: {},
                },
            )

        fields = {
            vol.Optional(f"channel_{i}", default=f"Kanal {i + 1}"): str
            for i in range(self._num_channels)
        }
        return self.async_show_form(step_id="channel_names", data_schema=vol.Schema(fields))

    async def async_step_group_names(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Step 3: Name each group."""
        if user_input is not None:
            group_names = {str(i): user_input.get(f"group_{i}", f"Gruppe {i + 1}") for i in range(self._num_groups)}
            return self.async_create_entry(
                title=f"Jarolift ({self._host})",
                data={
                    CONF_HOST: self._host,
                    CONF_NUM_CHANNELS: self._num_channels,
                    CONF_NUM_GROUPS: self._num_groups,
                    CONF_CHANNEL_NAMES: self._channel_names,
                    CONF_GROUP_NAMES: group_names,
                },
            )

        fields = {
            vol.Optional(f"group_{i}", default=f"Gruppe {i + 1}"): str
            for i in range(self._num_groups)
        }
        return self.async_show_form(step_id="group_names", data_schema=vol.Schema(fields))
