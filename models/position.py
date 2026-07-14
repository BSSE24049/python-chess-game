# models/position.py

class Position:
    """Represents a coordinate (row, col) on an 8x8 chessboard.
    
    Coordinate System:
      - Row 0 corresponds to Chess Rank 8 (Top/Black back rank)
      - Row 7 corresponds to Chess Rank 1 (Bottom/White back rank)
      - Col 0 corresponds to Chess File 'a'
      - Col 7 corresponds to Chess File 'h'
    """
    
    def __init__(self, row: int, col: int):
        self.row = row
        self.col = col

    def is_valid(self) -> bool:
        """Returns True if the position is within the 8x8 board boundaries."""
        return 0 <= self.row < 8 and 0 <= self.col < 8

    def to_algebraic(self) -> str:
        """Converts the internal grid coordinates to algebraic notation (e.g. 'e4')."""
        if not self.is_valid():
            return "??"
        file_char = chr(ord('a') + self.col)
        rank_char = str(8 - self.row)
        return f"{file_char}{rank_char}"

    @staticmethod
    def from_algebraic(algebraic: str) -> 'Position':
        """Creates a Position from algebraic chess notation (e.g. 'e4')."""
        if len(algebraic) != 2:
            raise ValueError(f"Invalid algebraic coordinate: {algebraic}")
        col = ord(algebraic[0].lower()) - ord('a')
        row = 8 - int(algebraic[1])
        return Position(row, col)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Position):
            return False
        return self.row == other.row and self.col == other.col

    def __hash__(self) -> int:
        return hash((self.row, self.col))

    def __repr__(self) -> str:
        return f"Position(row={self.row}, col={self.col})"
