"""Jarolift Controller Home Assistant Integration."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    CONF_NUM_CHANNELS,
    CONF_NUM_GROUPS,
    CONF_CHANNEL_NAMES,
    CONF_GROUP_NAMES,
)
from .websocket_client import JaroliftWebSocket

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["cover", "button"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Jarolift from a config entry."""
    host = entry.data["host"]

    def on_status_update(status: dict) -> None:
        """Forward status updates to all listeners."""
        hass.bus.async_fire(f"{DOMAIN}_status_update", status)

    ws = JaroliftWebSocket(host, on_status_update)
    await ws.start()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "ws": ws,
        "host": host,
        "num_channels": entry.data.get(CONF_NUM_CHANNELS, 4),
        "num_groups": entry.data.get(CONF_NUM_GROUPS, 0),
        "channel_names": entry.data.get(CONF_CHANNEL_NAMES, {}),
        "group_names": entry.data.get(CONF_GROUP_NAMES, {}),
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id)
        await data["ws"].stop()

    return unload_ok
