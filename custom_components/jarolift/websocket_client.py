"""WebSocket client for Jarolift Controller."""
import asyncio
import json
import logging
from typing import Callable

import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

from .const import (
    WS_RECONNECT_INTERVAL,
    WS_TYPE_SEND_DATA,
    WS_TYPE_UPDATE_JSON,
    WS_TYPE_HEARTBEAT,
    ELEMENT_CHANNEL,
    ELEMENT_GROUP,
    ACTION_UP,
    ACTION_DOWN,
    ACTION_STOP,
    ACTION_SHADE,
)

_LOGGER = logging.getLogger(__name__)


class JaroliftWebSocket:
    """Manages the WebSocket connection to the Jarolift ESP32 Controller."""

    def __init__(self, host: str, on_status_update: Callable) -> None:
        self._host = host
        self._uri = f"ws://{host}/ws"
        self._ws = None
        self._running = False
        self._on_status_update = on_status_update
        self._task = None
        self._status: dict = {}

    async def start(self) -> None:
        """Start the WebSocket listener loop."""
        self._running = True
        self._task = asyncio.create_task(self._listen_loop())

    async def stop(self) -> None:
        """Stop the WebSocket listener loop."""
        self._running = False
        if self._ws:
            await self._ws.close()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _listen_loop(self) -> None:
        """Reconnect loop that keeps the connection alive."""
        while self._running:
            try:
                _LOGGER.debug("Connecting to %s", self._uri)
                async with websockets.connect(self._uri) as ws:
                    self._ws = ws
                    _LOGGER.info("Connected to Jarolift Controller at %s", self._host)
                    async for raw in ws:
                        await self._handle_message(raw)
            except (ConnectionClosed, WebSocketException, OSError) as err:
                _LOGGER.warning("WebSocket disconnected (%s), retrying in %ds", err, WS_RECONNECT_INTERVAL)
                self._ws = None
            except asyncio.CancelledError:
                break
            except Exception as err:  # noqa: BLE001
                _LOGGER.error("Unexpected WebSocket error: %s", err)
                self._ws = None

            if self._running:
                await asyncio.sleep(WS_RECONNECT_INTERVAL)

    async def _handle_message(self, raw: str) -> None:
        """Parse incoming WebSocket messages."""
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            _LOGGER.debug("Non-JSON message: %s", raw)
            return

        msg_type = msg.get("type")

        if msg_type == WS_TYPE_UPDATE_JSON:
            self._status.update(msg)
            self._on_status_update(self._status)

        elif msg_type == WS_TYPE_HEARTBEAT:
            _LOGGER.debug("Heartbeat received")

    async def _send(self, element_id: str) -> None:
        """Send a sendData command."""
        if not self._ws:
            _LOGGER.warning("Cannot send command - WebSocket not connected")
            return
        msg = {
            "type": WS_TYPE_SEND_DATA,
            "elementId": element_id,
            "value": "true",
        }
        try:
            await self._ws.send(json.dumps(msg))
            _LOGGER.debug("Sent: %s", msg)
        except (ConnectionClosed, WebSocketException) as err:
            _LOGGER.error("Failed to send command: %s", err)

    # --- Channel commands ---

    async def channel_up(self, channel: int) -> None:
        await self._send(f"{ELEMENT_CHANNEL}_{ACTION_UP}_{channel}")

    async def channel_down(self, channel: int) -> None:
        await self._send(f"{ELEMENT_CHANNEL}_{ACTION_DOWN}_{channel}")

    async def channel_stop(self, channel: int) -> None:
        await self._send(f"{ELEMENT_CHANNEL}_{ACTION_STOP}_{channel}")

    async def channel_shade(self, channel: int) -> None:
        await self._send(f"{ELEMENT_CHANNEL}_{ACTION_SHADE}_{channel}")

    # --- Group commands ---

    async def group_up(self, group: int) -> None:
        await self._send(f"{ELEMENT_GROUP}_{ACTION_UP}_{group}")

    async def group_down(self, group: int) -> None:
        await self._send(f"{ELEMENT_GROUP}_{ACTION_DOWN}_{group}")

    async def group_stop(self, group: int) -> None:
        await self._send(f"{ELEMENT_GROUP}_{ACTION_STOP}_{group}")

    async def group_shade(self, group: int) -> None:
        await self._send(f"{ELEMENT_GROUP}_{ACTION_SHADE}_{group}")

    @property
    def connected(self) -> bool:
        return self._ws is not None

    @property
    def status(self) -> dict:
        return self._status

    async def async_test_connection(self) -> bool:
        """Test if the controller is reachable."""
        try:
            async with websockets.connect(self._uri, open_timeout=5) as ws:
                await asyncio.wait_for(ws.recv(), timeout=3)
            return True
        except Exception:  # noqa: BLE001
            return False
