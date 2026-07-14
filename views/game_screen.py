# views/game_screen.py
import tkinter as tk
from tkinter import messagebox
import theme
from models.position import Position
from controllers.game import ChessGame

class GameScreen(tk.Frame):
    """The main gameplay screen displaying the board, clocks, move log, and controls."""
    
    def __init__(self, parent, game: ChessGame, on_new_game_callback):
        super().__init__(parent, bg=theme.BG_MAIN)
        self.parent = parent
        self.game = game
        self.on_new_game = on_new_game_callback
        
        self.square_size = 65
        self.board_offset = 25
        self.after_id = None
        self.promotion_active = False
        self.piece_images = {}
        self.game_over_popup = None

        self.create_layout()
        self.draw_board()
        self.start_timer_loop()
        
        # Start async assets download
        import threading
        threading.Thread(target=self.download_assets_bg, daemon=True).start()

    def create_layout(self):
        # 1. Header Frame
        header = tk.Frame(self, bg=theme.BG_HEADER, height=60, bd=0)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)
        
        title_label = tk.Label(
            header, 
            text="♔  CHESS  ♚", 
            font=theme.FONT_HEADER, 
            bg=theme.BG_HEADER, 
            fg=theme.COLOR_GOLD
        )
        title_label.pack(side="left", padx=20)
        
        # Thin gold separator line below header
        separator = tk.Frame(self, bg=theme.COLOR_GOLD, height=1)
        separator.pack(fill="x")

        # New Game Button
        new_game_btn = tk.Button(
            header, 
            text="New Game", 
            font=theme.FONT_LABEL_BOLD, 
            bg=theme.BG_PANEL, 
            fg=theme.COLOR_GOLD, 
            activebackground=theme.COLOR_GOLD,
            activeforeground=theme.BG_CONTAINER,
            bd=0,
            highlightthickness=1,
            highlightbackground=theme.COLOR_GOLD,
            padx=15, 
            pady=5, 
            cursor="hand2",
            command=self.trigger_new_game
        )
        new_game_btn.pack(side="right", padx=20, pady=12)
        new_game_btn.bind("<Enter>", lambda e: new_game_btn.configure(bg=theme.COLOR_GOLD, fg=theme.BG_CONTAINER))
        new_game_btn.bind("<Leave>", lambda e: new_game_btn.configure(bg=theme.BG_PANEL, fg=theme.COLOR_GOLD))

        # Main Workspace Container
        workspace = tk.Frame(self, bg=theme.BG_MAIN)
        workspace.pack(fill="both", expand=True, padx=20, pady=20)

        # Column 1: Left Panel (Timers & Players)
        left_panel = tk.Frame(workspace, bg=theme.BG_MAIN, width=180)
        left_panel.pack(side="left", fill="y", padx=(0, 20))
        left_panel.pack_propagate(False)

        # Player 1 - White pieces side
        self.p1_frame = tk.Frame(
            left_panel, 
            bg=theme.BG_PANEL, 
            bd=0,
            highlightthickness=2,
            highlightbackground=theme.BG_MAIN
        )
        self.p1_frame.pack(fill="x", pady=(20, 20), ipady=15)
        
        # White color indicator accent
        p1_accent = tk.Frame(self.p1_frame, bg="#f0f2f5", width=4)
        p1_accent.pack(side="left", fill="y")
        
        p1_info = tk.Frame(self.p1_frame, bg=theme.BG_PANEL)
        p1_info.pack(side="left", fill="both", expand=True)
        
        self.p1_name_lbl = tk.Label(p1_info, text="♙  " + self.game.players["white"].name, font=theme.FONT_LABEL_BOLD, bg=theme.BG_PANEL, fg=theme.TEXT_LIGHT)
        self.p1_name_lbl.pack(anchor="w", padx=12, pady=(10, 5))
        
        self.p1_time_lbl = tk.Label(p1_info, text=self.game.players["white"].format_time(), font=theme.FONT_TIMER, bg=theme.BG_PANEL, fg=theme.TEXT_LIGHT)
        self.p1_time_lbl.pack(anchor="w", padx=12)

        # Player 2 - Black pieces side
        self.p2_frame = tk.Frame(
            left_panel, 
            bg=theme.BG_PANEL, 
            bd=0,
            highlightthickness=2,
            highlightbackground=theme.BG_MAIN
        )
        self.p2_frame.pack(fill="x", pady=(0, 20), ipady=15)
        
        # Dark color indicator accent
        p2_accent = tk.Frame(self.p2_frame, bg="#3a3b3d", width=4)
        p2_accent.pack(side="left", fill="y")
        
        p2_info = tk.Frame(self.p2_frame, bg=theme.BG_PANEL)
        p2_info.pack(side="left", fill="both", expand=True)
        
        self.p2_name_lbl = tk.Label(p2_info, text="♟  " + self.game.players["black"].name, font=theme.FONT_LABEL_BOLD, bg=theme.BG_PANEL, fg=theme.TEXT_MUTED)
        self.p2_name_lbl.pack(anchor="w", padx=12, pady=(10, 5))
        
        self.p2_time_lbl = tk.Label(p2_info, text=self.game.players["black"].format_time(), font=theme.FONT_TIMER, bg=theme.BG_PANEL, fg=theme.TEXT_MUTED)
        self.p2_time_lbl.pack(anchor="w", padx=12)

        # Column 2: Board Canvas Panel
        center_panel = tk.Frame(workspace, bg=theme.BG_MAIN)
        center_panel.pack(side="left", fill="both", expand=True)

        canvas_dim = self.square_size * 8 + self.board_offset * 2
        self.canvas = tk.Canvas(
            center_panel, 
            width=canvas_dim, 
            height=canvas_dim, 
            bg=theme.BG_MAIN, 
            bd=0, 
            highlightthickness=0
        )
        self.canvas.pack(anchor="center")
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        # Bottom Status Notification Line & Results Button
        self.status_frame = tk.Frame(center_panel, bg=theme.BG_MAIN)
        self.status_frame.pack(pady=5)
        
        self.status_lbl = tk.Label(
            self.status_frame, 
            text="White's Turn", 
            font=theme.FONT_LABEL_BOLD, 
            bg=theme.BG_MAIN, 
            fg=theme.TEXT_LIGHT
        )
        self.status_lbl.pack(side="left")
        
        self.results_btn = tk.Button(
            self.status_frame,
            text="🏆 Show Results",
            font=theme.FONT_LABEL_BOLD,
            bg=theme.BG_PANEL,
            fg=theme.COLOR_GOLD,
            activebackground=theme.COLOR_GOLD,
            activeforeground=theme.BG_CONTAINER,
            bd=0,
            padx=10,
            pady=2,
            cursor="hand2",
            command=self.show_game_over_overlay
        )
        # Note: We won't pack results_btn initially, we will manage packing dynamically in sync_game_state_ui

        # Column 3: Right Panel (Move Log & History controls)
        right_panel = tk.Frame(workspace, bg=theme.BG_MAIN, width=280)
        right_panel.pack(side="left", fill="y", padx=(20, 0))
        right_panel.pack_propagate(False)

        history_title = tk.Label(right_panel, text="Move History", font=theme.FONT_LABEL_BOLD, bg=theme.BG_MAIN, fg=theme.COLOR_GOLD)
        history_title.pack(anchor="center", pady=(10, 10))

        # Listbox & Scrollbar inside a Frame
        list_container = tk.Frame(right_panel, bg=theme.BG_PANEL)
        list_container.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(list_container, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        self.history_listbox = tk.Listbox(
            list_container, 
            yscrollcommand=scrollbar.set, 
            bg=theme.BG_PANEL, 
            fg=theme.TEXT_LIGHT, 
            selectbackground=theme.COLOR_GOLD, 
            selectforeground=theme.BG_CONTAINER,
            font=theme.FONT_MONO, 
            bd=0, 
            highlightthickness=0
        )
        self.history_listbox.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.config(command=self.history_listbox.yview)

        # Undo / Redo controls frame
        controls = tk.Frame(right_panel, bg=theme.BG_MAIN, pady=10)
        controls.pack(fill="x")

        # Undo button
        self.undo_btn = tk.Button(
            controls, 
            text="◀  Undo", 
            font=theme.FONT_LABEL_BOLD, 
            bg=theme.BG_PANEL, 
            fg=theme.TEXT_LIGHT, 
            activebackground=theme.COLOR_GOLD,
            activeforeground=theme.BG_CONTAINER,
            bd=0, 
            padx=10, 
            pady=5, 
            cursor="hand2",
            command=self.trigger_undo
        )
        self.undo_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.undo_btn.bind("<Enter>", lambda e: self.undo_btn.configure(bg=theme.COLOR_GOLD, fg=theme.BG_CONTAINER))
        self.undo_btn.bind("<Leave>", lambda e: self.undo_btn.configure(bg=theme.BG_PANEL, fg=theme.TEXT_LIGHT))

        # Redo button
        self.redo_btn = tk.Button(
            controls, 
            text="Redo  ▶", 
            font=theme.FONT_LABEL_BOLD, 
            bg=theme.BG_PANEL, 
            fg=theme.TEXT_LIGHT, 
            activebackground=theme.COLOR_GOLD,
            activeforeground=theme.BG_CONTAINER,
            bd=0, 
            padx=10, 
            pady=5, 
            cursor="hand2",
            command=self.trigger_redo
        )
        self.redo_btn.pack(side="left", fill="x", expand=True, padx=(5, 0))
        self.redo_btn.bind("<Enter>", lambda e: self.redo_btn.configure(bg=theme.COLOR_GOLD, fg=theme.BG_CONTAINER))
        self.redo_btn.bind("<Leave>", lambda e: self.redo_btn.configure(bg=theme.BG_PANEL, fg=theme.TEXT_LIGHT))

    def draw_board(self):
        """Clears and redraws the chessboard squares, coordinates, highlights, and pieces."""
        self.canvas.delete("all")
        
        # Draw Gold Border
        board_size = self.square_size * 8
        self.canvas.create_rectangle(
            self.board_offset - 2, 
            self.board_offset - 2, 
            self.board_offset + board_size + 2, 
            self.board_offset + board_size + 2, 
            outline=theme.BOARD_BORDER, 
            width=2
        )

        # Draw squares & highlights
        for r in range(8):
            for c in range(8):
                # Calculate pixel coords
                x1 = self.board_offset + c * self.square_size
                y1 = self.board_offset + r * self.square_size
                x2 = x1 + self.square_size
                y2 = y1 + self.square_size

                # Square Base Color
                color = theme.BOARD_LIGHT if (r + c) % 2 == 0 else theme.BOARD_DARK
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

                # Highlight previous move squares
                last_move = self.game.board.get_last_move()
                if last_move and (Position(r, c) == last_move.start_pos or Position(r, c) == last_move.end_pos):
                    # Faded yellow outline for previous move
                    self.canvas.create_rectangle(x1 + 1, y1 + 1, x2 - 1, y2 - 1, outline=theme.BOARD_PREV_MOVE, width=2)

                # Highlight selection
                if self.game.selected_position and self.game.selected_position == Position(r, c):
                    self.canvas.create_rectangle(x1 + 1, y1 + 1, x2 - 1, y2 - 1, outline=theme.BOARD_HIGHLIGHT, width=3)

        # Draw Ranks coordinates (Numbers on left)
        for r in range(8):
            y = self.board_offset + r * self.square_size + self.square_size / 2
            rank_text = str(8 - r)
            self.canvas.create_text(
                self.board_offset / 2, 
                y, 
                text=rank_text, 
                font=theme.FONT_LABEL_BOLD, 
                fill=theme.TEXT_MUTED
            )

        # Draw Files coordinates (Letters on bottom)
        for c in range(8):
            x = self.board_offset + c * self.square_size + self.square_size / 2
            file_text = chr(ord('a') + c)
            self.canvas.create_text(
                x, 
                self.board_offset + board_size + self.board_offset / 2, 
                text=file_text.upper(), 
                font=theme.FONT_LABEL_BOLD, 
                fill=theme.TEXT_MUTED
            )

        # Draw Pieces
        for r in range(8):
            for c in range(8):
                piece = self.game.board.get_piece(Position(r, c))
                if piece:
                    x = self.board_offset + c * self.square_size + self.square_size / 2
                    y = self.board_offset + r * self.square_size + self.square_size / 2
                    
                    # Convert piece to 2-character code (e.g. 'wp', 'bk')
                    color_char = "w" if piece.color == "white" else "b"
                    if piece.__class__.__name__ == "Knight":
                        type_char = "n"
                    else:
                        type_char = piece.__class__.__name__[0].lower()
                    code = f"{color_char}{type_char}"
                    
                    # If image is loaded, draw it!
                    if hasattr(self, 'piece_images') and code in self.piece_images:
                        self.canvas.create_image(x, y, image=self.piece_images[code])
                    else:
                        # Fallback to high-quality drop-shadow unicode characters
                        unicode_symbol = piece.get_unicode_char()
                        # White pieces: color white. Black pieces: color black.
                        text_fill = "#ffffff" if piece.color == "white" else "#1e1e1e"
                        
                        # Draw shadow first (3D pop effect)
                        self.canvas.create_text(
                            x + 2, 
                            y + 2, 
                            text=unicode_symbol, 
                            font=(theme.FONT_CHESS, 38), 
                            fill="#151515" if piece.color == "white" else "#d0d0d0"
                        )
                        # Draw piece
                        self.canvas.create_text(
                            x, 
                            y, 
                            text=unicode_symbol, 
                            font=(theme.FONT_CHESS, 38), 
                            fill=text_fill
                        )

        # Draw Legal moves destinations
        if self.game.selected_position:
            for move_dest in self.game.highlighted_moves:
                cx = self.board_offset + move_dest.col * self.square_size + self.square_size / 2
                cy = self.board_offset + move_dest.row * self.square_size + self.square_size / 2
                
                # Check if target is a capture or empty
                is_capture = self.game.board.get_piece(move_dest) is not None
                
                if is_capture:
                    # Draw a circular ring around the square
                    self.canvas.create_oval(
                        cx - self.square_size/2 + 4, 
                        cy - self.square_size/2 + 4, 
                        cx + self.square_size/2 - 4, 
                        cy + self.square_size/2 - 4, 
                        outline=theme.COLOR_GREEN, 
                        width=3
                    )
                else:
                    # Draw a solid dot
                    self.canvas.create_oval(
                        cx - 8, 
                        cy - 8, 
                        cx + 8, 
                        cy + 8, 
                        fill=theme.BOARD_VALID_DOT, 
                        outline=""
                    )

    def on_canvas_click(self, event):
        """Resolves canvas clicks to board positions and routes to the game selection logic."""
        if self.game.state != "playing" or self.promotion_active:
            return
            
        # Convert pixel to col, row
        col = int((event.x - self.board_offset) // self.square_size)
        row = int((event.y - self.board_offset) // self.square_size)
        
        click_pos = Position(row, col)
        if not click_pos.is_valid():
            return
            
        # Check if the click executes a promotion move
        if click_pos in self.game.highlighted_moves and self.game.check_promotion_needed(click_pos):
            # Prompt the overlay
            self.display_promotion_overlay(click_pos)
            return

        # Route standard select
        needs_redraw = self.game.select_square(click_pos)
        if needs_redraw:
            self.draw_board()
            self.sync_game_state_ui()

    def display_promotion_overlay(self, promotion_pos: Position):
        """Draws an overlay selection frame for choosing pawn promotion piece."""
        self.promotion_active = True
        
        self.promo_frame = tk.Frame(
            self, 
            bg=theme.BG_HEADER, 
            bd=2, 
            relief="solid", 
            highlightbackground=theme.COLOR_GOLD, 
            highlightthickness=1
        )
        # Position in middle of board
        self.promo_frame.place(relx=0.5, rely=0.5, anchor="center", width=320, height=100)
        
        prompt_lbl = tk.Label(self.promo_frame, text="Select Promotion Piece:", font=theme.FONT_LABEL_BOLD, bg=theme.BG_HEADER, fg=theme.TEXT_LIGHT)
        prompt_lbl.pack(side="top", pady=5)
        
        choices = [
            ("Queen", "♛"), 
            ("Rook", "♜"), 
            ("Bishop", "♝"), 
            ("Knight", "♞")
        ]
        
        btn_frame = tk.Frame(self.promo_frame, bg=theme.BG_HEADER)
        btn_frame.pack(side="top", fill="x", expand=True)
        
        for name, sym in choices:
            btn = tk.Button(
                btn_frame, 
                text=sym, 
                font=(theme.FONT_CHESS, 20),
                bg=theme.BG_PANEL, 
                fg=theme.TEXT_LIGHT, 
                activebackground=theme.COLOR_GOLD,
                activeforeground=theme.BG_CONTAINER,
                bd=0, 
                width=3, 
                cursor="hand2"
            )
            # Bind closure selection
            btn.config(command=lambda n=name: self.resolve_promotion(promotion_pos, n))
            btn.pack(side="left", expand=True, padx=5, pady=5)
            # Add small closures for hover highlights
            self._bind_hover(btn, theme.COLOR_BLUE, theme.BG_PANEL)

    def _bind_hover(self, widget, hover_color, normal_color):
        widget.bind("<Enter>", lambda e: widget.configure(bg=hover_color))
        widget.bind("<Leave>", lambda e: widget.configure(bg=normal_color))

    def resolve_promotion(self, dest: Position, choice: str):
        """Finalizes the move with promotion selection, removing the overlay."""
        self.promo_frame.destroy()
        self.promotion_active = False
        
        self.game.execute_move_from_selection(dest, choice)
        self.draw_board()
        self.sync_game_state_ui()

    def sync_game_state_ui(self):
        """Synchronizes UI elements (timer active borders, move log, undo/redo states)."""
        # Active Player Panel highlights + timer text brightness
        if self.game.current_turn == "white":
            self.p1_frame.configure(highlightbackground=theme.COLOR_GOLD)
            self.p2_frame.configure(highlightbackground=theme.BG_MAIN)
            self.p1_time_lbl.configure(fg=theme.TEXT_LIGHT)
            self.p2_time_lbl.configure(fg=theme.TEXT_MUTED)
        else:
            self.p1_frame.configure(highlightbackground=theme.BG_MAIN)
            self.p2_frame.configure(highlightbackground=theme.COLOR_GOLD)
            self.p1_time_lbl.configure(fg=theme.TEXT_MUTED)
            self.p2_time_lbl.configure(fg=theme.TEXT_LIGHT)

        # Update turn / state message
        if self.game.state == "playing":
            # If the user Undid a checkmate move, destroy the popup
            self.hide_game_over_overlay()
            
            active_name = self.game.get_active_player().name
            color_cap = self.game.current_turn.capitalize()
            if self.game.board.is_in_check(self.game.current_turn):
                self.status_lbl.configure(text=f"Check! {active_name}'s turn ({color_cap})", fg=theme.COLOR_GOLD)
            else:
                self.status_lbl.configure(text=f"{active_name}'s turn ({color_cap})", fg=theme.TEXT_LIGHT)
        else:
            self.status_lbl.configure(text=self.game.win_reason or "Game Over", fg=theme.COLOR_GOLD)
            # Pop up Game Over modal if not already visible
            if self.game_over_popup is None:
                self.show_game_over_overlay()

        # Show or hide results button next to status line
        if self.game.state != "playing" and self.game_over_popup is None:
            self.results_btn.pack(side="left", padx=10)
        else:
            self.results_btn.pack_forget()

        # Sync Move log listbox
        self.history_listbox.delete(0, tk.END)
        for idx, move in enumerate(self.game.board.move_history):
            # Display moves paired as e.g. "1. Aliha: Pawn e2 to e4"
            player_name = self.game.players[move.piece_moved.color].name
            color_tag = "W" if move.piece_moved.color == "white" else "B"
            desc = move.to_readable_string()
            move_num = (idx // 2) + 1
            
            if idx % 2 == 0:
                self.history_listbox.insert(tk.END, f"{move_num}. [{color_tag}] {player_name}: {desc}")
            else:
                # Add offset spaces for Black's move under White's move
                self.history_listbox.insert(tk.END, f"   [{color_tag}] {player_name}: {desc}")
                
        # Scroll to bottom
        self.history_listbox.see(tk.END)

        # Toggle Undo/Redo button visual availability states
        if len(self.game.board.move_history) > 0:
            self.undo_btn.configure(state="normal", cursor="hand2")
        else:
            self.undo_btn.configure(state="disabled", cursor="arrow")

        if len(self.game.redo_stack) > 0:
            self.redo_btn.configure(state="normal", cursor="hand2")
        else:
            self.redo_btn.configure(state="disabled", cursor="arrow")

    def start_timer_loop(self):
        """Initializes the periodic ticking schedule."""
        self.tick()

    def tick(self):
        """Decrements the active timer, refreshes clock labels, and recurs."""
        self.game.handle_tick()
        
        # Refresh Labels
        self.p1_time_lbl.configure(text=self.game.players["white"].format_time())
        self.p2_time_lbl.configure(text=self.game.players["black"].format_time())
        
        # Check if clock caused game over
        if self.game.state == "timeout":
            self.status_lbl.configure(text=self.game.win_reason, fg=theme.COLOR_GOLD)
            
        self.after_id = self.after(100, self.tick)

    def trigger_undo(self):
        """Fires Undo, redrawing the canvas and updating logs."""
        if self.promotion_active:
            return
        if self.game.undo():
            self.draw_board()
            self.sync_game_state_ui()

    def trigger_redo(self):
        """Fires Redo, redrawing the canvas and updating logs."""
        if self.promotion_active:
            return
        if self.game.redo():
            self.draw_board()
            self.sync_game_state_ui()

    def trigger_new_game(self):
        """Halts the ticking loops and alerts the controller callback to reset."""
        if messagebox.askyesno("New Game", "Are you sure you want to end this game and start a new one?"):
            self.cleanup()
            self.on_new_game()

    def cleanup(self):
        """Kills any active scheduled tick loops to prevent thread leaks."""
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None
        self.hide_game_over_overlay()

    def download_assets_bg(self):
        """Asynchronously downloads Chess.com piece image assets if they do not exist locally."""
        import os
        import urllib.request
        
        assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
        if not os.path.exists(assets_dir):
            os.makedirs(assets_dir)
            
        pieces = [
            "wk", "wq", "wr", "wb", "wn", "wp",
            "bk", "bq", "br", "bb", "bn", "bp"
        ]
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        for p in pieces:
            local_path = os.path.join(assets_dir, f"{p}.png")
            if not os.path.exists(local_path):
                url = f"https://www.chess.com/chess-themes/pieces/neo/60/{p}.png"
                try:
                    req = urllib.request.Request(url, headers=headers)
                    with urllib.request.urlopen(req, timeout=5) as response:
                        with open(local_path, "wb") as f:
                            f.write(response.read())
                except Exception as e:
                    print(f"Failed to download asset {p}: {e}")
                    
        # Load images and refresh board in the main thread
        self.after(0, self.load_images_and_refresh)

    def load_images_and_refresh(self):
        """Loads downloaded PNG images from assets/ directory into PhotoImage references."""
        import os
        assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
        
        pieces = [
            "wk", "wq", "wr", "wb", "wn", "wp",
            "bk", "bq", "br", "bb", "bn", "bp"
        ]
        
        self.piece_images = {}
        for p in pieces:
            local_path = os.path.join(assets_dir, f"{p}.png")
            if os.path.exists(local_path):
                try:
                    self.piece_images[p] = tk.PhotoImage(file=local_path)
                except Exception as e:
                    print(f"Error loading Image {p}: {e}")
                    
        # Redraw the board with the new images
        self.draw_board()

    def show_game_over_overlay(self):
        """Displays a highly visible game-over announcement banner in the center."""
        self.hide_game_over_overlay()
        
        self.game_over_popup = tk.Frame(
            self, 
            bg=theme.BG_HEADER, 
            bd=3, 
            relief="solid", 
            highlightbackground=theme.COLOR_GOLD, 
            highlightthickness=1
        )
        self.game_over_popup.place(relx=0.5, rely=0.5, anchor="center", width=380, height=220)
        
        # Trophy icon / Title
        trophy_lbl = tk.Label(
            self.game_over_popup, 
            text="🏆  GAME OVER  🏆", 
            font=("Segoe UI", 16, "bold"), 
            bg=theme.BG_HEADER, 
            fg=theme.COLOR_GOLD
        )
        trophy_lbl.pack(pady=(15, 10))
        
        # Winner text
        status_text = self.game.win_reason or "The game has ended."
        status_lbl = tk.Label(
            self.game_over_popup, 
            text=status_text, 
            font=("Segoe UI", 13, "bold"), 
            bg=theme.BG_HEADER, 
            fg=theme.TEXT_LIGHT,
            wraplength=340,
            justify="center"
        )
        status_lbl.pack(pady=10)
        
        # Action Buttons frame
        btn_frame = tk.Frame(self.game_over_popup, bg=theme.BG_HEADER)
        btn_frame.pack(side="bottom", fill="x", pady=(0, 15), padx=20)
        
        # View Board Button (closes overlay to let player inspect final board state)
        view_board_btn = tk.Button(
            btn_frame,
            text="Review Board",
            font=theme.FONT_LABEL_BOLD,
            bg=theme.BG_PANEL,
            fg=theme.TEXT_LIGHT,
            activebackground=theme.COLOR_BLUE,
            activeforeground=theme.TEXT_LIGHT,
            bd=0,
            padx=10,
            pady=5,
            cursor="hand2",
            command=self.hide_game_over_overlay
        )
        view_board_btn.pack(side="left", expand=True, fill="x", padx=(0, 5))
        self._bind_hover(view_board_btn, theme.COLOR_BLUE, theme.BG_PANEL)
        
        # Rematch / New Game Button
        new_game_btn = tk.Button(
            btn_frame,
            text="New Game",
            font=theme.FONT_LABEL_BOLD,
            bg=theme.COLOR_GOLD,
            fg=theme.BG_CONTAINER,
            activebackground="#e67e22",
            activeforeground=theme.BG_CONTAINER,
            bd=0,
            padx=10,
            pady=5,
            cursor="hand2",
            command=self.trigger_new_game
        )
        new_game_btn.pack(side="left", expand=True, fill="x", padx=(5, 0))
        self._bind_hover(new_game_btn, "#e67e22", theme.COLOR_GOLD)

    def hide_game_over_overlay(self):
        """Destroys the popup screen overlay if it exists."""
        if self.game_over_popup:
            self.game_over_popup.destroy()
            self.game_over_popup = None
