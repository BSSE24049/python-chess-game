# main.py
import tkinter as tk
import theme
from controllers.game import ChessGame
from views.start_screen import StartScreen
from views.game_screen import GameScreen

class ChessApplication:
    """The central application class managing window settings and view switches."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Chess Game")
        self.root.configure(bg=theme.BG_MAIN)
        
        # Adjust dimensions for 1120x680 workspace, centered
        self.width = 1120
        self.height = 680
        self.center_window()
        
        # Prevent resizing to maintain precise layout coordinates
        self.root.resizable(False, False)
        
        # Instantiate controller
        self.game = ChessGame()
        self.current_frame = None
        
        # Show setup screen initially
        self.show_start_screen()

    def center_window(self):
        """Calculates monitor dimensions and centers the window."""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        x = (screen_width - self.width) // 2
        y = (screen_height - self.height) // 2
        
        self.root.geometry(f"{self.width}x{self.height}+{x}+{y}")

    def show_start_screen(self):
        """Displays the names and timers setup screen."""
        self.clear_frame()
        self.root.title("Chess Game — Setup")
        
        self.current_frame = StartScreen(
            parent=self.root, 
            on_start_callback=self.start_game
        )
        self.current_frame.pack(fill="both", expand=True)

    def start_game(self, white_name: str, black_name: str, time_limit_seconds: float):
        """Transition callback that configures game state and loads the chess board screen."""
        self.clear_frame()
        
        # Set dynamic title
        self.root.title(f"Chess Game — {white_name} vs {black_name}")
        
        # Setup controller values
        self.game.initialize_game(white_name, black_name, time_limit_seconds)
        
        # Load gameplay view
        self.current_frame = GameScreen(
            parent=self.root, 
            game=self.game, 
            on_new_game_callback=self.show_start_screen
        )
        self.current_frame.pack(fill="both", expand=True)
        self.current_frame.sync_game_state_ui()

    def clear_frame(self):
        """Removes the active view frame and cleans up memory."""
        if self.current_frame:
            # If the current frame has a cleanup function (like GameScreen's timer cancellation), run it
            if hasattr(self.current_frame, "cleanup"):
                self.current_frame.cleanup()
            self.current_frame.destroy()
            self.current_frame = None

    def run(self):
        """Starts the Tkinter application event loop."""
        self.root.mainloop()

if __name__ == "__main__":
    app = ChessApplication()
    app.run()
