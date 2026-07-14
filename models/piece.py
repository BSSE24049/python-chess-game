# models/piece.py
from abc import ABC, abstractmethod
from typing import List
from models.position import Position

class Piece(ABC):
    """Abstract base class representing a generic Chess Piece."""
    
    def __init__(self, color: str, position: Position):
        self.color = color          # "white" or "black"
        self.position = position    # Position object
        self.has_moved = False      # Tracked for castling and pawn double-steps

    @abstractmethod
    def get_valid_moves(self, board) -> List[Position]:
        """Calculates pseudo-legal moves based on piece movements, ignoring check safety.
        
        The Board class will filter these pseudo-legal moves to ensure they don't
        leave or place the piece's King in check.
        """
        pass

    @abstractmethod
    def get_unicode_char(self) -> str:
        """Returns the specific Unicode character for this piece type."""
        pass

    def clone(self) -> 'Piece':
        """Creates a copy of the piece (useful for simulating moves)."""
        cloned = self.__class__(self.color, Position(self.position.row, self.position.col))
        cloned.has_moved = self.has_moved
        return cloned

    def __repr__(self) -> str:
        return f"{self.color.capitalize()} {self.__class__.__name__} at {self.position.to_algebraic()}"


class Pawn(Piece):
    """Pawn piece rules and movement logic."""
    
    def get_valid_moves(self, board) -> List[Position]:
        moves = []
        row, col = self.position.row, self.position.col
        
        # White moves "up" (row decreases), Black moves "down" (row increases)
        direction = -1 if self.color == "white" else 1
        
        # 1. Single step forward
        fwd_1 = Position(row + direction, col)
        if fwd_1.is_valid() and board.get_piece(fwd_1) is None:
            moves.append(fwd_1)
            
            # 2. Double step forward (only from starting rows)
            start_row = 6 if self.color == "white" else 1
            if row == start_row:
                fwd_2 = Position(row + 2 * direction, col)
                if fwd_2.is_valid() and board.get_piece(fwd_2) is None:
                    moves.append(fwd_2)
                    
        # 3. Standard Diagonal Captures
        for col_offset in [-1, 1]:
            diag_pos = Position(row + direction, col + col_offset)
            if diag_pos.is_valid():
                target_piece = board.get_piece(diag_pos)
                if target_piece and target_piece.color != self.color:
                    moves.append(diag_pos)
                    
        # 4. En Passant Capture (DSA Check: historical last move evaluation)
        # Condition: Opponent pawn did a double-step in the previous turn and landed adjacent to this pawn.
        last_move = board.get_last_move()
        if last_move:
            prev_piece = last_move.piece_moved
            if isinstance(prev_piece, Pawn) and abs(last_move.start_pos.row - last_move.end_pos.row) == 2:
                # The opponent pawn is adjacent on the same row
                if last_move.end_pos.row == row and abs(last_move.end_pos.col - col) == 1:
                    # En passant target square is behind the opponent pawn
                    ep_target = Position(row + direction, last_move.end_pos.col)
                    moves.append(ep_target)
                    
        return moves

    def get_unicode_char(self) -> str:
        return "♙" if self.color == "white" else "♟"


class Knight(Piece):
    """Knight piece rules (fixed-offset leaps, jumping over pieces)."""
    
    def get_valid_moves(self, board) -> List[Position]:
        moves = []
        row, col = self.position.row, self.position.col
        
        # 8 possible L-shaped jumps
        offsets = [
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1)
        ]
        
        for dr, dc in offsets:
            target_pos = Position(row + dr, col + dc)
            if target_pos.is_valid():
                target_piece = board.get_piece(target_pos)
                if target_piece is None or target_piece.color != self.color:
                    moves.append(target_pos)
                    
        return moves

    def get_unicode_char(self) -> str:
        return "♘" if self.color == "white" else "♞"


class Bishop(Piece):
    """Bishop piece rules (sliding diagonally)."""
    
    def get_valid_moves(self, board) -> List[Position]:
        moves = []
        row, col = self.position.row, self.position.col
        
        # 4 diagonal vectors
        vectors = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        
        # DSA Algorithm: Grid raycast traversal
        for dr, dc in vectors:
            step = 1
            while True:
                target_pos = Position(row + dr * step, col + dc * step)
                if not target_pos.is_valid():
                    break
                target_piece = board.get_piece(target_pos)
                if target_piece is None:
                    moves.append(target_pos)
                else:
                    if target_piece.color != self.color:
                        moves.append(target_pos)  # Capture opponent
                    break  # Blocked by teammate or opponent
                step += 1
                
        return moves

    def get_unicode_char(self) -> str:
        return "♗" if self.color == "white" else "♝"


class Rook(Piece):
    """Rook piece rules (sliding horizontally/vertically)."""
    
    def get_valid_moves(self, board) -> List[Position]:
        moves = []
        row, col = self.position.row, self.position.col
        
        # 4 orthogonal vectors
        vectors = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        
        # DSA Algorithm: Grid raycast traversal
        for dr, dc in vectors:
            step = 1
            while True:
                target_pos = Position(row + dr * step, col + dc * step)
                if not target_pos.is_valid():
                    break
                target_piece = board.get_piece(target_pos)
                if target_piece is None:
                    moves.append(target_pos)
                else:
                    if target_piece.color != self.color:
                        moves.append(target_pos)  # Capture opponent
                    break  # Blocked by teammate or opponent
                step += 1
                
        return moves

    def get_unicode_char(self) -> str:
        return "♖" if self.color == "white" else "♜"


class Queen(Piece):
    """Queen piece rules (combination of Bishop and Rook sliding moves)."""
    
    def get_valid_moves(self, board) -> List[Position]:
        moves = []
        row, col = self.position.row, self.position.col
        
        # 8 direction vectors
        vectors = [
            (1, 0), (-1, 0), (0, 1), (0, -1),
            (1, 1), (1, -1), (-1, 1), (-1, -1)
        ]
        
        # DSA Algorithm: Grid raycast traversal
        for dr, dc in vectors:
            step = 1
            while True:
                target_pos = Position(row + dr * step, col + dc * step)
                if not target_pos.is_valid():
                    break
                target_piece = board.get_piece(target_pos)
                if target_piece is None:
                    moves.append(target_pos)
                else:
                    if target_piece.color != self.color:
                        moves.append(target_pos)  # Capture opponent
                    break  # Blocked by teammate or opponent
                step += 1
                
        return moves

    def get_unicode_char(self) -> str:
        return "♕" if self.color == "white" else "♛"


class King(Piece):
    """King piece rules (single step plus castling validation)."""
    
    def get_valid_moves(self, board) -> List[Position]:
        moves = []
        row, col = self.position.row, self.position.col
        
        # 8 directions, 1 step
        offsets = [
            (1, 0), (-1, 0), (0, 1), (0, -1),
            (1, 1), (1, -1), (-1, 1), (-1, -1)
        ]
        
        for dr, dc in offsets:
            target_pos = Position(row + dr, col + dc)
            if target_pos.is_valid():
                target_piece = board.get_piece(target_pos)
                if target_piece is None or target_piece.color != self.color:
                    moves.append(target_pos)
                    
        # Castling validation is handled dynamically by board checking,
        # but the King class can offer the potential castling squares to the checker.
        # White start: row 7, col 4. Black start: row 0, col 4.
        if not self.has_moved:
            # Kingside Castling
            # Rook must be at col 7
            ks_rook = board.get_piece(Position(row, 7))
            if isinstance(ks_rook, Rook) and not ks_rook.has_moved:
                # Path between them must be empty: cols 5 and 6
                if board.get_piece(Position(row, 5)) is None and board.get_piece(Position(row, 6)) is None:
                    moves.append(Position(row, 6))
                    
            # Queenside Castling
            # Rook must be at col 0
            qs_rook = board.get_piece(Position(row, 0))
            if isinstance(qs_rook, Rook) and not qs_rook.has_moved:
                # Path between them must be empty: cols 1, 2, and 3
                if (board.get_piece(Position(row, 1)) is None and 
                    board.get_piece(Position(row, 2)) is None and 
                    board.get_piece(Position(row, 3)) is None):
                    moves.append(Position(row, 2))
                    
        return moves

    def get_unicode_char(self) -> str:
        return "♔" if self.color == "white" else "♚"
