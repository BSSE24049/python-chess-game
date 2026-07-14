# models/player.py

class Player:
    """Represents a player in the chess game, tracking their name, color, and timer."""
    
    def __init__(self, name: str, color: str, initial_time_seconds: float):
        self.name = name
        self.color = color                      # "white" or "black"
        self.time_left = initial_time_seconds    # In seconds (e.g. 300 for 5 minutes)
        
    def decrement_time(self, seconds: float):
        """Decrements the player's remaining time, clamping at zero."""
        self.time_left = max(0.0, self.time_left - seconds)

    def is_out_of_time(self) -> bool:
        """Returns True if the player's timer has run out."""
        return self.time_left <= 0.0

    def format_time(self) -> str:
        """Formats the remaining time into MM:SS format (e.g. '04:59')."""
        total_seconds = int(self.time_left)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def __repr__(self) -> str:
        return f"Player({self.name}, {self.color.capitalize()}, Time={self.format_time()})"
