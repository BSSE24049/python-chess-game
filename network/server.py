# network/server.py
"""
Chess Multiplayer Relay Server
================================
Lightweight WebSocket server that manages game rooms and relays moves.
Each room has exactly 2 players. The server validates nothing — it only relays.

Run with:
    python network/server.py
Or via the launcher:
    python network/start_server.py
"""

import asyncio
import json
import random
import string
import sys
import os

# Allow running from project root OR from within network/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import websockets
except ImportError:
    print("ERROR: 'websockets' library not installed.")
    print("Run:  pip install websockets")
    sys.exit(1)

from network.protocol import DEFAULT_SERVER_HOST, DEFAULT_SERVER_PORT

# ─── Room Registry ────────────────────────────────────────────────────────────
# Structure: { "ABC123": {"players": [ws1, ws2], "names": ["Aliha", "Zoya"]} }
rooms: dict = {}


def generate_code(length: int = 6) -> str:
    """Generate a unique, readable room code (no confusable characters)."""
    chars = (string.ascii_uppercase + string.digits).translate(
        str.maketrans("", "", "0O1IL")  # Remove ambiguous chars
    )
    return "".join(random.choices(chars, k=length))


# ─── Connection Handler ───────────────────────────────────────────────────────
async def handler(websocket):
    """Handles one WebSocket connection through its entire lifetime."""
    room_code: str | None = None

    try:
        async for raw_msg in websocket:
            try:
                msg = json.loads(raw_msg)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type")

            # ── Host: Create a new room ────────────────────────────────────
            if msg_type == "host":
                if room_code:
                    continue  # Already in a room

                code = generate_code()
                while code in rooms:
                    code = generate_code()

                room_code = code
                rooms[room_code] = {
                    "players": [websocket],
                    "names": [msg.get("name", "Player 1")],
                }
                await websocket.send(json.dumps({"type": "room_created", "code": room_code}))
                print(f"[+] Room created: {room_code}  (host: {rooms[room_code]['names'][0]})")

            # ── Join: Enter an existing room ───────────────────────────────
            elif msg_type == "join":
                code = msg.get("code", "").upper().strip()
                player_name = msg.get("name", "Player 2")

                if code not in rooms:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": f"Game code '{code}' not found. Ask the host to share it again."
                    }))
                    continue

                room = rooms[code]
                if len(room["players"]) >= 2:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "This game room is already full."
                    }))
                    continue

                room_code = code
                room["players"].append(websocket)
                room["names"].append(player_name)

                host_ws, guest_ws = room["players"]
                host_name, guest_name = room["names"]

                # Host is always White, guest is always Black
                await host_ws.send(json.dumps({
                    "type": "game_start",
                    "color": "white",
                    "opponent": guest_name,
                }))
                await guest_ws.send(json.dumps({
                    "type": "game_start",
                    "color": "black",
                    "opponent": host_name,
                }))
                print(f"[►] Game started in {room_code}:  {host_name} (White) vs {guest_name} (Black)")

            # ── Move: Relay to the other player ───────────────────────────
            elif msg_type == "move":
                if room_code and room_code in rooms:
                    for p_ws in rooms[room_code]["players"]:
                        if p_ws != websocket:
                            await p_ws.send(raw_msg)  # Relay as-is

    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as exc:
        print(f"[!] Unexpected error: {exc}")
    finally:
        # Notify the other player and clean up
        if room_code and room_code in rooms:
            room = rooms[room_code]
            for p_ws in room["players"]:
                if p_ws != websocket:
                    try:
                        await p_ws.send(json.dumps({"type": "opponent_disconnected"}))
                    except Exception:
                        pass
            del rooms[room_code]
            print(f"[-] Room {room_code} closed.")


# ─── Entry Point ──────────────────────────────────────────────────────────────
async def main():
    import socket
    # Try to get the LAN IP to display for users
    try:
        lan_ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        lan_ip = "your-ip-address"

    print("=" * 52)
    print("    Chess Multiplayer Server")
    print("=" * 52)
    print(f"  Local address : ws://localhost:{DEFAULT_SERVER_PORT}")
    print(f"  LAN address   : ws://{lan_ip}:{DEFAULT_SERVER_PORT}")
    print()
    print("  For internet play, use ngrok:")
    print(f"    ngrok tcp {DEFAULT_SERVER_PORT}")
    print()
    print("  Press Ctrl+C to stop the server.")
    print("=" * 52)

    async with websockets.serve(handler, DEFAULT_SERVER_HOST, DEFAULT_SERVER_PORT):
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped.")
