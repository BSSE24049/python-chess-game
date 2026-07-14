# controllers/game.py
from typing import List, Optional, Dict
import time

from models.board import Board
from models.position import Position
from models.move import Move
from models.player import Player
from models.piece import Piece, Pawn, King
import sound

class ChessGame:
    """Orchestrates game state, player turns, timers, and Undo/Redo stacks."""
    
    def __init__(self):
        self.board = Board()
        self.players: Dict[str, Optional[Player]] = {"white": None, "black": None}
        self.current_turn = "white"
        
        # State: "setup", "playing", "checkmate", "stalemate", "draw", "timeout"
        self.state = "setup"
        self.winner: Optional[str] = None
        self.win_reason: Optional[str] = None
        
        # Selection state
        self.selected_position: Optional[Position] = None
        self.highlighted_moves: List[Position] = []
        
        # DSA: Redo Stack
        self.redo_stack: List[Move] = []
        
        # Online multiplayer state
        self.online_mode: bool = False
        self.network_client = None      # NetworkClient instance
        self.my_color: Optional[str] = None  # "white" or "black" in online mode
        
        # Clock tracking
        self.last_clock_tick: float = 0.0
        self.timer_enabled = True

    def initialize_game(self, white_name: str, black_name: str, time_limit_seconds: float,
                         network_client=None, my_color: Optional[str] = None):
        """Initializes a new game session with players, timer, and optional online mode."""
        self.board.reset_board()
        self.players["white"] = Player(white_name or "White Player", "white", time_limit_seconds)
        self.players["black"] = Player(black_name or "Black Player", "black", time_limit_seconds)
        self.current_turn = "white"
        self.state = "playing"
        self.winner = None
        self.win_reason = None
        self.selected_position = None
        self.highlighted_moves = []
        self.redo_stack = []
        self.timer_enabled = time_limit_seconds > 0
        self.last_clock_tick = time.time()
        
        # Online mode setup
        self.online_mode = network_client is not None
        self.network_client = network_client
        self.my_color = my_color

    def get_active_player(self) -> Optional[Player]:
        """Returns the player whose turn it currently is."""
        return self.players[self.current_turn]

    def get_inactive_player(self) -> Optional[Player]:
        """Returns the player who is waiting."""
        inactive_color = "black" if self.current_turn == "white" else "white"
        return self.players[inactive_color]

    def handle_tick(self):
        """Ticks the game timer for the active player, calling game over if timeout occurs."""
        if self.state != "playing" or not self.timer_enabled:
            return
            
        current_time = time.time()
        elapsed = current_time - self.last_clock_tick
        self.last_clock_tick = current_time
        
        active_player = self.get_active_player()
        if active_player:
            active_player.decrement_time(elapsed)
            if active_player.is_out_of_time():
                self.state = "timeout"
                inactive_player = self.get_inactive_player()
                self.winner = inactive_player.color if inactive_player else "draw"
                self.win_reason = f"Timeout! {active_player.name} ran out of time."
                sound.play_game_over()

    def reset_tick_timer(self):
        """Resets the benchmark time for clock ticking (call when turns swap)."""
        self.last_clock_tick = time.time()

    def select_square(self, position: Position) -> bool:
        """Handles selecting/deselecting cells.
        Returns True if the board view needs refreshing.
        """
        if self.state != "playing":
            return False
        
        # In online mode, only allow interaction on YOUR turn
        if self.online_mode and self.current_turn != self.my_color:
            return False

        piece = self.board.get_piece(position)

        # Case 1: A piece was already selected
        if self.selected_position:
            # If clicked a highlighted move, execute the move!
            if position in self.highlighted_moves:
                self.execute_move_from_selection(position)
                return True
            
            # If clicked player's own piece, change selection to it
            elif piece and piece.color == self.current_turn:
                self.selected_position = position
                self.highlighted_moves = self.board.get_legal_moves(piece)
                return True
                
            # If clicked anything else, deselect
            else:
                self.selected_position = None
                self.highlighted_moves = []
                return True

        # Case 2: No piece selected yet, player clicks their own piece
        else:
            if piece and piece.color == self.current_turn:
                self.selected_position = position
                self.highlighted_moves = self.board.get_legal_moves(piece)
                return True
                
        return False

    def check_promotion_needed(self, end_pos: Position) -> bool:
        """Checks if a movement from selection will prompt pawn promotion."""
        if not self.selected_position:
            return False
        piece = self.board.get_piece(self.selected_position)
        if isinstance(piece, Pawn) and (end_pos.row == 0 or end_pos.row == 7):
            return True
        return False

    def execute_move_from_selection(self, end_pos: Position, promo_choice: str = "Queen",
                                     from_network: bool = False):
        """Performs the move from the selected square to the destination square.
        
        from_network=True suppresses the network send to avoid echo-loops.
        """
        if not self.selected_position:
            return
            
        start_pos = self.selected_position
        piece = self.board.get_piece(start_pos)
        if not piece:
            return
            
        captured_piece = self.board.get_piece(end_pos)
        is_ep = isinstance(piece, Pawn) and end_pos.col != start_pos.col and captured_piece is None
        is_cast = isinstance(piece, King) and abs(end_pos.col - start_pos.col) == 2
        is_prom = isinstance(piece, Pawn) and (end_pos.row == 0 or end_pos.row == 7)

        move = Move(
            start_pos=start_pos,
            end_pos=end_pos,
            piece_moved=piece,
            piece_captured=captured_piece,
            is_en_passant=is_ep,
            is_castling=is_cast,
            is_promotion=is_prom,
            promoted_to=promo_choice if is_prom else None
        )
        
        # Execute the move on the board
        self.board.make_move(move, real=True)
        
        # Clear Redo stack as a new move was made
        self.redo_stack.clear()
        
        # Reset selection
        self.selected_position = None
        self.highlighted_moves = []
        
        # ── Send move over network (only for locally made moves) ──────────
        if not from_network and self.online_mode and self.network_client:
            self.network_client.send_move(
                start_pos.to_algebraic(),
                end_pos.to_algebraic(),
                promo_choice if is_prom else None
            )
        
        # Sound Effects
        if self.board.is_in_check("black" if self.current_turn == "white" else "white"):
            sound.play_check()
        elif move.piece_captured or move.is_en_passant:
            sound.play_capture()
        else:
            sound.play_move()

        # Check for game-ending conditions
        next_turn_color = "black" if self.current_turn == "white" else "white"
        if self.board.is_checkmate(next_turn_color):
            self.state = "checkmate"
            self.winner = self.current_turn
            self.win_reason = f"Checkmate! {self.players[self.current_turn].name} wins."
            sound.play_game_over()
        elif self.board.is_stalemate(next_turn_color):
            self.state = "stalemate"
            self.winner = "draw"
            self.win_reason = "Draw! Stalemate (no legal moves)."
            sound.play_game_over()
        elif self.board.is_insufficient_material():
            self.state = "draw"
            self.winner = "draw"
            self.win_reason = "Draw! Insufficient mating material."
            sound.play_game_over()
        else:
            # Swap Turn
            self.current_turn = next_turn_color
            self.reset_tick_timer()

    def undo(self) -> bool:
        """DSA Undo: Pops from move stack, reverts board state, pushes to Redo stack.
        Disabled in online mode to prevent sync issues.
        """
        if self.online_mode:
            return False   # Cannot undo in an online game
        if not self.board.move_history:
            return False
            
        move = self.board.move_history[-1]
        self.board.unmake_move(move, real=True)
        
        # Push to redo stack
        self.redo_stack.append(move)
        
        # Reset selection
        self.selected_position = None
        self.highlighted_moves = []
        
        # Toggle turn back
        self.current_turn = "black" if self.current_turn == "white" else "white"
        self.state = "playing"  # Resume playing if we were game-over
        self.winner = None
        self.win_reason = None
        self.reset_tick_timer()
        sound.play_move()
        return True

    def redo(self) -> bool:
        """DSA Redo: Pops from Redo stack, makes move on board, pushes to Move history.
        
        Returns True if successful.
        """
        if not self.redo_stack:
            return False
            
        move = self.redo_stack.pop()
        self.board.make_move(move, real=True)
        
        # Reset selection
        self.selected_position = None
        self.highlighted_moves = []
        
        # Toggle turn forward
        self.current_turn = "black" if self.current_turn == "white" else "white"
        
        # Check game states
        next_turn_color = "black" if self.current_turn == "white" else "white"
        if self.board.is_checkmate(next_turn_color):
            self.state = "checkmate"
            self.winner = "black" if self.current_turn == "white" else "white"
            self.win_reason = f"Checkmate! Winner determined."
            sound.play_game_over()
        elif self.board.is_stalemate(next_turn_color):
            self.state = "stalemate"
            self.winner = "draw"
            self.win_reason = "Stalemate draw."
            sound.play_game_over()
        elif self.board.is_insufficient_material():
            self.state = "draw"
            self.winner = "draw"
            self.win_reason = "Insufficient material draw."
            sound.play_game_over()
            
        self.reset_tick_timer()
        sound.play_move()
        return True

    def apply_network_move(self, start_alg: str, end_alg: str, promotion: Optional[str] = None):
        """Apply a move received from the network (opponent's move in online mode).
        
        Converts algebraic notation to Position objects, temporarily sets the
        game selection state, and delegates to execute_move_from_selection with
        from_network=True so the move is NOT echoed back to the server.
        """
        start_pos = Position.from_algebraic(start_alg)
        end_pos   = Position.from_algebraic(end_alg)
        
        # Prime the selection state
        self.selected_position = start_pos
        self.highlighted_moves = [end_pos]
        
        # Execute — passing from_network=True prevents re-sending
        self.execute_move_from_selection(end_pos, promotion or "Queen", from_network=True)
