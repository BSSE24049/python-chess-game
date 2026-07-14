# 2-Player Chess Game in Python

A beautifully-crafted, dark-themed, 2-player desktop Chess game written in Python using the standard `tkinter` graphics framework. 

This project implements standard chess rules (including check, checkmate, stalemate, draws, castling, en passant, and pawn promotion) and applies **Object-Oriented Programming (OOP)** and **Data Structures and Algorithms (DSA)** concepts.

---

## 🎨 Features & UI/UX
- **Modern Dark Theme**: Custom aesthetic featuring deep slate navy colors and metallic gold highlights matching professional layouts.
- **Dynamic Clocks**: Active turn countdown clocks for both players (supporting custom limits: 1m, 3m, 5m, 10m, 30m, or casual untimed).
- **Move History Log**: Displays chronologically formatted moves in algebraic notation.
- **Undo / Redo Buttons**: Complete board state traversal using historical stacks.
- **In-App Pawn Promotion**: Overlay window directly on the canvas allowing users to select Queen, Rook, Bishop, or Knight promotions.
- **Audio Feedback**: Non-blocking audio sounds played on background threads for standard moves, captures, checks, and game-over states.

---

## 🏗️ Project Architecture & OOP Concepts
The code is designed following modular Object-Oriented principles, drawing inspiration from standard model-view-controller (MVC) structures:

1. **Abstraction**:
   - The [`Piece`](models/piece.py) class is an abstract base class (`abc.ABC`) declaring general piece interfaces. It cannot be instantiated directly.
2. **Inheritance**:
   - Subclasses ([`Pawn`](models/piece.py), [`Knight`](models/piece.py), [`Bishop`](models/piece.py), [`Rook`](models/piece.py), [`Queen`](models/piece.py), and [`King`](models/piece.py)) inherit from `Piece` and override core functionalities.
3. **Polymorphism**:
   - The [`Board`](models/board.py) class processes piece interactions polymorphically. By invoking `piece.get_valid_moves(board)` on any piece reference, the board gets custom movement coordinates without knowing the piece's concrete type.
4. **Encapsulation**:
   - Game attributes and states are protected inside their respective classes (`Player`, `Move`, `Board`, `ChessGame`), exposing only explicit control methods to outer packages.

---

## 🧠 Applied Data Structures & Algorithms (DSA)
This project serves as a practical demonstration of standard DSA concepts:

1. **2D Grid (Matrix)**:
   - The chessboard is represented as an 8x8 matrix (`self.grid` in [`board.py`](models/board.py)) containing `Piece` object references or `None`. This allows $O(1)$ constant time lookups for pieces at coordinate rows and columns.
2. **Stack (Undo/Redo History)**:
   - When a move is completed, it is packed into a [`Move`](models/move.py) object (acting as a data node preserving start, end, captured pieces, and movement flags) and pushed onto a **Move Stack** (`self.move_history`).
   - When you click **Undo**, the game pops the top move off the history stack, reverts the board's state, and pushes it onto a **Redo Stack** (`self.redo_stack`).
   - Making any new manual move clears the Redo Stack, preserving tree-branching history rules.
3. **Grid Vector Traversal (Pathfinding)**:
   - Sliding pieces (Bishops, Rooks, Queens) generate valid moves by tracing coordinates along directional offset vectors (e.g. $(+1, -1)$) until they encounter an obstacle or the edge of the matrix.
4. **Backtracking (Check Safety Verification)**:
   - To verify if a pseudo-legal move is safe to make (i.e. does not place or leave the player's own King in check):
     1. The board performs a **simulated move** changing the grid positions.
     2. It checks if the opponent attacks the King's square in this new arrangement.
     3. It **backtracks (reverts the move)**, restoring the grid references and original positions.
     4. If the King was in check during the simulation, the move is declared illegal.
5. **State-Space Search (Checkmate & Stalemate Detection)**:
   - The board detects checkmate and stalemate by checking all available pieces for the active color, generating their legal moves, simulating them, and checking if any legal configuration exists. If the size of the state-space search returns `0` legal moves, the game transitions to game over.

---

## 🚀 How to Run the Game

### Prerequisites
You need **Python 3.x** installed on your system. 

#### Installing Python (if not already installed)
1. Open a terminal or Command Prompt.
2. If running python displays the Microsoft Store download page, complete the download from the store, OR download the installer directly from the official [python.org downloads](https://www.python.org/downloads/) page and run it.
3. **Important**: When running the installer, ensure the checkbox **"Add Python to PATH"** is ticked before clicking Install.

### Running the game
1. Clone or extract this project folder to your system.
2. Open Command Prompt or PowerShell in this folder, and run:
   ```cmd
   python main.py
   ```
3. (Alternative) Open this folder in **VS Code**, open `main.py`, and click the **Run** button in the top right corner.
