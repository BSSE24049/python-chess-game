# models/board.py
from typing import List, Optional
from models.position import Position
from models.move import Move
from models.piece import Piece, Pawn, Knight, Bishop, Rook, Queen, King

class Board:
    """Manages the 8x8 grid of chess pieces, move simulations, and state validation.
    
    This class is the core repository of the board's state. It implements:
      - A 2D Grid (list of lists) representing the board
      - Backtracking algorithms (simulate move, verify check, revert state)
      - State-space search for Checkmate/Stalemate
    """
    
    def __init__(self):
        # 8x8 grid initialized to None
        self.grid: List[List[Optional[Piece]]] = [[None for _ in range(8)] for _ in range(8)]
        self.move_history: List[Move] = []
        self.reset_board()

    def reset_board(self):
        """Places all chess pieces in their standard starting positions."""
        self.grid = [[None for _ in range(8)] for _ in range(8)]
        self.move_history = []

        # Setup Black pieces (Row 0: Back rank, Row 1: Pawns)
        self.grid[0][0] = Rook("black", Position(0, 0))
        self.grid[0][1] = Knight("black", Position(0, 1))
        self.grid[0][2] = Bishop("black", Position(0, 2))
        self.grid[0][3] = Queen("black", Position(0, 3))
        self.grid[0][4] = King("black", Position(0, 4))
        self.grid[0][5] = Bishop("black", Position(0, 5))
        self.grid[0][6] = Knight("black", Position(0, 6))
        self.grid[0][7] = Rook("black", Position(0, 7))
        for col in range(8):
            self.grid[1][col] = Pawn("black", Position(1, col))

        # Setup White pieces (Row 7: Back rank, Row 6: Pawns)
        self.grid[7][0] = Rook("white", Position(7, 0))
        self.grid[7][1] = Knight("white", Position(7, 1))
        self.grid[7][2] = Bishop("white", Position(7, 2))
        self.grid[7][3] = Queen("white", Position(7, 3))
        self.grid[7][4] = King("white", Position(7, 4))
        self.grid[7][5] = Bishop("white", Position(7, 5))
        self.grid[7][6] = Knight("white", Position(7, 6))
        self.grid[7][7] = Rook("white", Position(7, 7))
        for col in range(8):
            self.grid[6][col] = Pawn("white", Position(6, col))

    def get_piece(self, position: Position) -> Optional[Piece]:
        """Gets the piece at a given Position. Returns None if empty or invalid."""
        if not position.is_valid():
            return None
        return self.grid[position.row][position.col]

    def set_piece(self, position: Position, piece: Optional[Piece]):
        """Sets a piece at a given Position on the grid."""
        if position.is_valid():
            self.grid[position.row][position.col] = piece
            if piece:
                piece.position = position

    def get_last_move(self) -> Optional[Move]:
        """Returns the last completed move from the history stack, or None."""
        if self.move_history:
            return self.move_history[-1]
        return None

    def find_king(self, color: str) -> Optional[King]:
        """Finds and returns the King piece of the specified color."""
        for row in range(8):
            for col in range(8):
                piece = self.grid[row][col]
                if isinstance(piece, King) and piece.color == color:
                    return piece
        return None

    def is_square_attacked(self, position: Position, by_color: str) -> bool:
        """DSA Helper: Checks if any piece of by_color can attack the target position."""
        for row in range(8):
            for col in range(8):
                piece = self.grid[row][col]
                if piece and piece.color == by_color:
                    # Pawns capture diagonally, get_valid_moves handles captures
                    # but en-passant/forward steps are non-captures.
                    # For attack checking, handle pawn attacks explicitly.
                    if isinstance(piece, Pawn):
                        direction = -1 if piece.color == "white" else 1
                        pawn_row = piece.position.row + direction
                        pawn_cols = [piece.position.col - 1, piece.position.col + 1]
                        if position.row == pawn_row and position.col in pawn_cols:
                            return True
                    else:
                        # For other pieces, if they have pseudo-legal moves hitting position,
                        # the square is attacked. Note: We ignore castling here as it's not an attack.
                        pseudo_moves = piece.get_valid_moves(self)
                        if position in pseudo_moves:
                            return True
        return False

    def is_in_check(self, color: str) -> bool:
        """Returns True if the King of the specified color is under attack."""
        king = self.find_king(color)
        if not king:
            return False
        opponent_color = "black" if color == "white" else "white"
        return self.is_square_attacked(king.position, opponent_color)

    def make_move(self, move: Move, real: bool = True):
        """Executes a move on the board, updating grid references.
        
        If 'real' is True, pushes the move to the move_history stack.
        """
        # Get start/end positions and variables
        start = move.start_pos
        end = move.end_pos
        piece = move.piece_moved
        
        # 1. En Passant Capture Handling
        if move.is_en_passant:
            # Pawn is captured in the column of end_pos, but row of start_pos
            capture_row = start.row
            capture_col = end.col
            captured_pawn = self.grid[capture_row][capture_col]
            move.piece_captured = captured_pawn
            self.grid[capture_row][capture_col] = None

        # 2. Standard Capture handling
        # Captured piece is already stored in move.piece_captured by move creation
        # but let's make sure it is cleared from grid
        self.grid[start.row][start.col] = None
        
        # 3. Castling Handling (King & Rook move)
        if move.is_castling:
            self.grid[end.row][end.col] = piece
            piece.position = end
            
            # Identify rook coordinates
            row = start.row
            if end.col == 6:  # Kingside
                rook = self.grid[row][7]
                self.grid[row][7] = None
                self.grid[row][5] = rook
                if rook:
                    rook.position = Position(row, 5)
                    rook.has_moved = True
            elif end.col == 2:  # Queenside
                rook = self.grid[row][0]
                self.grid[row][0] = None
                self.grid[row][3] = rook
                if rook:
                    rook.position = Position(row, 3)
                    rook.has_moved = True
        
        # 4. Promotion Handling (Pawn turns into Queen/Rook/Bishop/Knight)
        elif move.is_promotion:
            promo_type = move.promoted_to or "Queen"
            color = piece.color
            if promo_type == "Queen":
                new_piece = Queen(color, end)
            elif promo_type == "Rook":
                new_piece = Rook(color, end)
            elif promo_type == "Bishop":
                new_piece = Bishop(color, end)
            elif promo_type == "Knight":
                new_piece = Knight(color, end)
            else:
                new_piece = Queen(color, end)
            
            new_piece.has_moved = True
            self.grid[end.row][end.col] = new_piece
        
        # 5. Normal Movement
        else:
            self.grid[end.row][end.col] = piece
            piece.position = end

        # Set has_moved flag on the primary moved piece
        piece.has_moved = True
        
        if real:
            self.move_history.append(move)

    def unmake_move(self, move: Move, real: bool = True):
        """DSA Backtracking Reversion: Reverts the board state back to before this move."""
        start = move.start_pos
        end = move.end_pos
        piece = move.piece_moved
        
        # Restore primary piece position and has_moved state
        self.grid[start.row][start.col] = piece
        piece.position = start
        piece.has_moved = move.prev_has_moved
        
        # Clear the destination
        self.grid[end.row][end.col] = None

        # Revert Castling Rook
        if move.is_castling:
            row = start.row
            if end.col == 6:  # Kingside
                rook = self.grid[row][5]
                self.grid[row][5] = None
                self.grid[row][7] = rook
                if rook:
                    rook.position = Position(row, 7)
                    rook.has_moved = False
            elif end.col == 2:  # Queenside
                rook = self.grid[row][3]
                self.grid[row][3] = None
                self.grid[row][0] = rook
                if rook:
                    rook.position = Position(row, 0)
                    rook.has_moved = False

        # Revert En Passant Captured Pawn
        elif move.is_en_passant:
            capture_row = start.row
            capture_col = end.col
            captured_pawn = move.piece_captured
            self.grid[capture_row][capture_col] = captured_pawn
            if captured_pawn:
                captured_pawn.position = Position(capture_row, capture_col)
                captured_pawn.has_moved = move.captured_prev_has_moved

        # Revert Standard Capture
        elif move.piece_captured:
            captured = move.piece_captured
            self.grid[end.row][end.col] = captured
            captured.position = end
            captured.has_moved = move.captured_prev_has_moved

        if real and self.move_history:
            self.move_history.pop()

    def is_move_legal(self, move: Move) -> bool:
        """DSA Backtracking Algorithm: Simulates move, checks for King safety, then reverts.
        
        Returns True if the move is legal (doesn't leave or place own King in check).
        """
        piece = move.piece_moved
        color = piece.color
        
        # Additional castling validation rules:
        # Cannot castle:
        # - While in check
        # - Through squares attacked by opponent
        # - Into check
        if move.is_castling:
            opponent = "black" if color == "white" else "white"
            if self.is_in_check(color):
                return False
            
            row = move.start_pos.row
            # Check squares the King traverses:
            if move.end_pos.col == 6:  # Kingside
                traversed_cols = [5, 6]  # f1, g1 / f8, g8
            else:  # Queenside
                traversed_cols = [3, 2]  # d1, c1 / d8, c8
                
            for col in traversed_cols:
                if self.is_square_attacked(Position(row, col), opponent):
                    return False

        # Simulating move
        self.make_move(move, real=False)
        in_check = self.is_in_check(color)
        # Backtracking
        self.unmake_move(move, real=False)
        
        return not in_check

    def get_legal_moves(self, piece: Piece) -> List[Position]:
        """Calculates all legitimate moves for a piece on the board."""
        pseudo_moves = piece.get_valid_moves(self)
        legal_destinations = []
        
        for dest in pseudo_moves:
            # Check if this destination leads to en passant, castling, promotion, etc.
            is_ep = False
            is_cast = False
            is_prom = False
            
            captured_piece = self.get_piece(dest)
            
            # En passant check
            if isinstance(piece, Pawn) and dest.col != piece.position.col and captured_piece is None:
                is_ep = True
                
            # Castling check
            if isinstance(piece, King) and abs(dest.col - piece.position.col) == 2:
                is_cast = True
                
            # Promotion check
            if isinstance(piece, Pawn) and (dest.row == 0 or dest.row == 7):
                is_prom = True
                
            simulated_move = Move(
                start_pos=piece.position,
                end_pos=dest,
                piece_moved=piece,
                piece_captured=captured_piece,
                is_en_passant=is_ep,
                is_castling=is_cast,
                is_promotion=is_prom
            )
            
            if self.is_move_legal(simulated_move):
                legal_destinations.append(dest)
                
        return legal_destinations

    def get_all_legal_moves(self, color: str) -> List[Move]:
        """DSA Search: Finds every legal move currently available for color."""
        moves = []
        for r in range(8):
            for c in range(8):
                piece = self.grid[r][c]
                if piece and piece.color == color:
                    legal_dests = self.get_legal_moves(piece)
                    for dest in legal_dests:
                        captured_piece = self.get_piece(dest)
                        is_ep = isinstance(piece, Pawn) and dest.col != piece.position.col and captured_piece is None
                        is_cast = isinstance(piece, King) and abs(dest.col - piece.position.col) == 2
                        is_prom = isinstance(piece, Pawn) and (dest.row == 0 or dest.row == 7)
                        
                        moves.append(Move(
                            start_pos=piece.position,
                            end_pos=dest,
                            piece_moved=piece,
                            piece_captured=captured_piece,
                            is_en_passant=is_ep,
                            is_castling=is_cast,
                            is_promotion=is_prom
                        ))
        return moves

    def is_checkmate(self, color: str) -> bool:
        """DSA Search: Returns True if color is in check and has no legal moves remaining."""
        if not self.is_in_check(color):
            return False
        # If in check, check if any piece has any legal moves
        return len(self.get_all_legal_moves(color)) == 0

    def is_stalemate(self, color: str) -> bool:
        """DSA Search: Returns True if color is NOT in check and has no legal moves remaining."""
        if self.is_in_check(color):
            return False
        return len(self.get_all_legal_moves(color)) == 0

    def is_insufficient_material(self) -> bool:
        """DSA Check: Detects standard draws from lack of mating force."""
        pieces = []
        for row in range(8):
            for col in range(8):
                p = self.grid[row][col]
                if p:
                    pieces.append(p)
                    
        # 1. King vs King
        if len(pieces) == 2:
            return True
            
        # 2. King + Knight vs King OR King + Bishop vs King
        if len(pieces) == 3:
            types = [p.__class__.__name__ for p in pieces]
            if "Knight" in types or "Bishop" in types:
                return True
                
        # 3. King + Bishop vs King + Bishop (on same-colored squares)
        if len(pieces) == 4:
            bishops = [p for p in pieces if isinstance(p, Bishop)]
            if len(bishops) == 2 and bishops[0].color != bishops[1].color:
                # Get cell colors of bishops
                sq1_color = (bishops[0].position.row + bishops[0].position.col) % 2
                sq2_color = (bishops[1].position.row + bishops[1].position.col) % 2
                if sq1_color == sq2_color:
                    return True
                    
        return False
