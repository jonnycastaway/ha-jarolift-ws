"""Cover platform for Jarolift Controller."""
import logging
from typing import Any

from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .websocket_client import JaroliftWebSocket

_LOGGER = logging.getLogger(__name__)

# Cover supports: open, close, stop + extra service for shade
SUPPORT_JAROLIFT = (
    CoverEntityFeature.OPEN
    | CoverEntityFeature.CLOSE
    | CoverEntityFeature.STOP
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Jarolift cover entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    ws: JaroliftWebSocket = data["ws"]
    host: str = data["host"]
    num_channels: int = data["num_channels"]
    num_groups: int = data["num_groups"]
    channel_names: dict = data["channel_names"]
    group_names: dict = data["group_names"]

    entities = []

    # Add channel covers
    for i in range(num_channels):
        name = channel_names.get(str(i), f"Kanal {i + 1}")
        entities.append(JaroliftCover(hass, ws, host, entry.entry_id, i, name, is_group=False))

    # Add group covers
    for i in range(num_groups):
        name = group_names.get(str(i), f"Gruppe {i + 1}")
        entities.append(JaroliftCover(hass, ws, host, entry.entry_id, i, name, is_group=True))

    async_add_entities(entities)

    # Register shade service
    async def handle_shade(call: Any) -> None:
        entity_id = call.data.get("entity_id")
        for entity in entities:
            if entity.entity_id == entity_id or entity_id is None:
                await entity.async_shade()

    hass.services.async_register(DOMAIN, "shade", handle_shade)


class JaroliftCover(CoverEntity):
    """Representation of a Jarolift roller shutter (channel or group)."""

    _attr_device_class = CoverDeviceClass.SHUTTER
    _attr_supported_features = SUPPORT_JAROLIFT
    _attr_is_closed = None  # unknown state (no feedback from motor)

    def __init__(
        self,
        hass: HomeAssistant,
        ws: JaroliftWebSocket,
        host: str,
        entry_id: str,
        index: int,
        name: str,
        is_group: bool,
    ) -> None:
        self._hass = hass
        self._ws = ws
        self._host = host
        self._index = index
        self._is_group = is_group
        self._attr_name = name

        kind = "group" if is_group else "channel"
        self._attr_unique_id = f"jarolift_{host}_{kind}_{index}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, host)},
            name="Jarolift Controller",
            manufacturer="dewenni",
            model="ESP32-Jarolift-Controller",
            configuration_url=f"http://{host}",
        )

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the shutter."""
        if self._is_group:
            await self._ws.group_up(self._index)
        else:
            await self._ws.channel_up(self._index)
        self._attr_is_closed = False
        self.async_write_ha_state()

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the shutter."""
        if self._is_group:
            await self._ws.group_down(self._index)
        else:
            await self._ws.channel_down(self._index)
        self._attr_is_closed = True
        self.async_write_ha_state()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the shutter."""
        if self._is_group:
            await self._ws.group_stop(self._index)
        else:
            await self._ws.channel_stop(self._index)
        self._attr_is_closed = None
        self.async_write_ha_state()

    async def async_shade(self) -> None:
        """Move shutter to shade position."""
        if self._is_group:
            await self._ws.group_shade(self._index)
        else:
            await self._ws.channel_shade(self._index)
        self._attr_is_closed = None
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra attributes."""
        return {
            "type": "group" if self._is_group else "channel",
            "index": self._index,
            "controller_ip": self._host,
        }
