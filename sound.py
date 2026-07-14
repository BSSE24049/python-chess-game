# sound.py
import sys
import threading

# We only import winsound on Windows to avoid crashes on other OS platforms
# though the user is on Windows, it is a good DSA / engineering practice to be cross-platform.
IS_WINDOWS = sys.platform.startswith("win")
if IS_WINDOWS:
    import winsound

def _play_beep(frequency, duration):
    """Internal helper to play beep."""
    if IS_WINDOWS:
        try:
            winsound.Beep(frequency, duration)
        except Exception:
            pass

def play_move():
    """Play sound for a standard piece move."""
    # Light high-pitch short beep
    threading.Thread(target=_play_beep, args=(800, 80), daemon=True).start()

def play_capture():
    """Play sound for a piece capture."""
    # Quick rising double-beep
    def run():
        _play_beep(900, 60)
        _play_beep(1100, 60)
    threading.Thread(target=run, daemon=True).start()

def play_check():
    """Play sound when a King is put in check."""
    # Staccato warning beep
    def run():
        _play_beep(500, 120)
        _play_beep(500, 120)
    threading.Thread(target=run, daemon=True).start()

def play_game_over():
    """Play sound when the game ends (checkmate, stalemate, or draw)."""
    # Descending victory/defeat tones
    def run():
        _play_beep(600, 150)
        _play_beep(500, 150)
        _play_beep(400, 300)
    threading.Thread(target=run, daemon=True).start()
