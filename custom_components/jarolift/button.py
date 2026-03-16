"""Button platform for Jarolift Controller – Schattenstellung."""
import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .websocket_client import JaroliftWebSocket

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Jarolift shade button entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    ws: JaroliftWebSocket = data["ws"]
    host: str = data["host"]
    num_channels: int = data["num_channels"]
    num_groups: int = data["num_groups"]
    channel_names: dict = data["channel_names"]
    group_names: dict = data["group_names"]

    entities = []

    for i in range(num_channels):
        name = channel_names.get(str(i), f"Kanal {i + 1}")
        entities.append(JaroliftShadeButton(ws, host, entry.entry_id, i, name, is_group=False))

    for i in range(num_groups):
        name = group_names.get(str(i), f"Gruppe {i + 1}")
        entities.append(JaroliftShadeButton(ws, host, entry.entry_id, i, name, is_group=True))

    async_add_entities(entities)


class JaroliftShadeButton(ButtonEntity):
    """Button that triggers the shade position for a channel or group."""

    _attr_icon = "mdi:sun-angle"

    def __init__(
        self,
        ws: JaroliftWebSocket,
        host: str,
        entry_id: str,
        index: int,
        name: str,
        is_group: bool,
    ) -> None:
        self._ws = ws
        self._host = host
        self._index = index
        self._is_group = is_group

        kind = "group" if is_group else "channel"
        self._attr_name = f"{name} Schattenstellung"
        self._attr_unique_id = f"jarolift_{host}_{kind}_{index}_shade"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, host)},
            name="Jarolift Controller",
            manufacturer="dewenni",
            model="ESP32-Jarolift-Controller",
            configuration_url=f"http://{host}",
        )

    async def async_press(self) -> None:
        """Send shade command when button is pressed."""
        if self._is_group:
            await self._ws.group_shade(self._index)
        else:
            await self._ws.channel_shade(self._index)
        _LOGGER.debug(
            "Shade triggered for %s %d",
            "group" if self._is_group else "channel",
            self._index,
        )
