# network/client.py
"""
Chess Network Client
======================
Thread-safe WebSocket client that runs an asyncio event loop in a background
daemon thread. All callbacks are dispatched back to the Tkinter main thread
via `tk_root.after(0, callback)` to ensure UI safety.
"""

import asyncio
import json
import threading
from typing import Callable, Optional

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False


class NetworkClient:
    """Manages the WebSocket connection to the chess relay server."""

    def __init__(self, server_url: str):
        self.server_url = server_url
        self.websocket = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self.connected: bool = False

        # ── Callbacks (all called on the main Tkinter thread) ──────────────
        self.on_room_created: Optional[Callable[[str], None]] = None
        self.on_game_start: Optional[Callable[[str, str], None]] = None
        self.on_move_received: Optional[Callable[[str, str, Optional[str]], None]] = None
        self.on_opponent_disconnected: Optional[Callable[[], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None

        # Set this to the Tkinter root window so callbacks are thread-safe
        self.tk_root = None

    # ─── Public API ──────────────────────────────────────────────────────────

    def connect_and_host(self, player_name: str):
        """Connect to the server and create a new game room."""
        self._ensure_loop()
        asyncio.run_coroutine_threadsafe(
            self._run({"type": "host", "name": player_name}),
            self.loop
        )

    def connect_and_join(self, player_name: str, code: str):
        """Connect to the server and join an existing room by code."""
        self._ensure_loop()
        asyncio.run_coroutine_threadsafe(
            self._run({"type": "join", "name": player_name, "code": code.upper().strip()}),
            self.loop
        )

    def send_move(self, start_alg: str, end_alg: str, promotion: Optional[str] = None):
        """Send a chess move to the opponent. Thread-safe."""
        if not (self.loop and self.websocket and self.connected):
            return
        msg: dict = {"type": "move", "start": start_alg, "end": end_alg}
        if promotion:
            msg["promotion"] = promotion
        asyncio.run_coroutine_threadsafe(
            self._send_raw(json.dumps(msg)),
            self.loop
        )

    def disconnect(self):
        """Close the WebSocket connection gracefully."""
        if self.websocket and self.loop:
            asyncio.run_coroutine_threadsafe(
                self.websocket.close(),
                self.loop
            )

    # ─── Internal Helpers ────────────────────────────────────────────────────

    def _ensure_loop(self):
        """Start the asyncio event loop in a background daemon thread."""
        if self.loop and self.loop.is_running():
            return
        self.loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self.loop.run_forever, daemon=True)
        self._thread.start()

    async def _run(self, initial_msg: dict):
        """Main async coroutine: connect, send the initial message, then listen."""
        try:
            async with websockets.connect(self.server_url, open_timeout=10) as ws:
                self.websocket = ws
                self.connected = True
                await ws.send(json.dumps(initial_msg))

                async for raw_msg in ws:
                    try:
                        msg = json.loads(raw_msg)
                        self._dispatch(msg)
                    except json.JSONDecodeError:
                        pass

        except Exception as exc:
            self._dispatch({"type": "error", "message": f"Connection failed: {exc}"})
        finally:
            self.connected = False
            self.websocket = None

    async def _send_raw(self, raw: str):
        if self.websocket:
            try:
                await self.websocket.send(raw)
            except Exception:
                pass

    def _dispatch(self, msg: dict):
        """Route an incoming message to the correct callback (main thread safe)."""
        msg_type = msg.get("type")

        def fire(cb, *args):
            if not cb:
                return
            if self.tk_root:
                self.tk_root.after(0, lambda: cb(*args))
            else:
                cb(*args)

        if msg_type == "room_created":
            fire(self.on_room_created, msg.get("code", ""))
        elif msg_type == "game_start":
            fire(self.on_game_start, msg.get("color", "white"), msg.get("opponent", "Opponent"))
        elif msg_type == "move":
            fire(self.on_move_received, msg.get("start"), msg.get("end"), msg.get("promotion"))
        elif msg_type == "opponent_disconnected":
            fire(self.on_opponent_disconnected)
        elif msg_type == "error":
            fire(self.on_error, msg.get("message", "Unknown error"))
