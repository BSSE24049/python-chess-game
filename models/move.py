# models/move.py
from typing import Optional
from models.position import Position

class Move:
    """Encapsulates all necessary details of a single chess move.
    
    This records the full historical state of the move to allow complete
    undo/redo capability by pushing and popping moves from a stack.
    """
    
    def __init__(self, 
                 start_pos: Position, 
                 end_pos: Position, 
                 piece_moved, 
                 piece_captured = None,
                 is_castling: bool = False,
                 is_en_passant: bool = False,
                 is_promotion: bool = False,
                 promoted_to: Optional[str] = None):
        
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.piece_moved = piece_moved
        self.piece_captured = piece_captured
        
        self.is_castling = is_castling
        self.is_en_passant = is_en_passant
        self.is_promotion = is_promotion
        self.promoted_to = promoted_to
        
        # Save state for restoration during Undo
        self.prev_has_moved = piece_moved.has_moved if piece_moved else False
        self.captured_prev_has_moved = piece_captured.has_moved if piece_captured else False

    def to_readable_string(self) -> str:
        """Returns a human-readable notation of the move for the game history pane."""
        piece_name = self.piece_moved.__class__.__name__
        start_alg = self.start_pos.to_algebraic()
        end_alg = self.end_pos.to_algebraic()
        
        action = "to"
        captured_text = ""
        if self.piece_captured:
            action = "takes"
            captured_name = self.piece_captured.__class__.__name__
            captured_text = f" {captured_name}"
            
        move_desc = f"{piece_name} {start_alg} {action}{captured_text} {end_alg}"
        
        if self.is_castling:
            side = "Kingside" if self.end_pos.col > self.start_pos.col else "Queenside"
            move_desc = f"Castled ({side})"
        elif self.is_en_passant:
            move_desc = f"Pawn {start_alg} takes Pawn {end_alg} (e.p.)"
        elif self.is_promotion:
            move_desc += f" (Promoted to {self.promoted_to})"
            
        return move_desc

    def __repr__(self) -> str:
        return f"Move({self.start_pos.to_algebraic()} -> {self.end_pos.to_algebraic()})"
