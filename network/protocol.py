# network/protocol.py
"""
Multiplayer Chess Network Protocol
===================================
All messages are JSON objects with a "type" field.

CLIENT → SERVER:
  {"type": "host", "name": "Aliha"}
      Host creates a new game room. Server generates a 6-char code.

  {"type": "join", "name": "Zoya", "code": "ABC123"}
      Guest joins an existing room using the shared code.

  {"type": "move", "start": "e2", "end": "e4", "promotion": null}
      Player sends their move (algebraic notation). Server relays to opponent.

SERVER → CLIENT:
  {"type": "room_created", "code": "ABC123"}
      Sent to the host after room creation. Display this code to share.

  {"type": "game_start", "color": "white", "opponent": "Zoya"}
      Sent to both players when the second player joins. Game can begin.

  {"type": "move", "start": "e7", "end": "e5", "promotion": null}
      Opponent's move relayed by the server.

  {"type": "opponent_disconnected"}
      Sent when the other player drops the connection.

  {"type": "error", "message": "Game code not found."}
      Error condition — room missing, full, etc.
"""

# ─── Message Type Constants ───────────────────────────────────────────────────
MSG_HOST                  = "host"
MSG_JOIN                  = "join"
MSG_MOVE                  = "move"
MSG_ROOM_CREATED          = "room_created"
MSG_GAME_START            = "game_start"
MSG_OPPONENT_DISCONNECTED = "opponent_disconnected"
MSG_ERROR                 = "error"

# ─── Server Defaults ──────────────────────────────────────────────────────────
DEFAULT_SERVER_HOST = "0.0.0.0"
DEFAULT_SERVER_PORT = 8765
DEFAULT_WS_URL      = "ws://localhost:8765"
