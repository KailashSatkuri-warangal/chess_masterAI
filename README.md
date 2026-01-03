# Chess Game

## Technologies used:
Python with pygame module

## Project Description:
This is a feature-rich Chess game built using Python with the Pygame module for the GUI. It offers multiple game modes and utilities for both casual play and learning.

### Game Modes:
1. **2 Player**: Play against another human locally.
2. **AI Mode**: Play against an AI powered by the Minimax algorithm with Alpha-Beta pruning. Supports multiple difficulty levels (Easy, Medium, Hard).
3. **Tutorial Mode**: Practice specific scenarios like "Mate in 1" or "Mate in 2" with AI assistance.
4. **Spectator Mode**: Watch the AI play against itself.

### Features:
- **Game Mechanics**: Full implementation of chess rules including Castling, En Passant, Pawn Promotion, Check, Checkmate, and Stalemate detection.
- **GUI**: Interactive board with legal move highlighting, move history log, and visual indicators for last moves.
- **Utilities**: 
  - Undo/Reset functionality.
  - Save and Load game state.
  - Pause/Resume.
  - Timer for both players.
  - Theme Selector (Classic, Green, Blue, Wood, Dark).
  - Sound effects for moves and captures.

## Files Description:

## How to Play

### Main Menu
-   **AI Mode**: Play against the computer. Choose difficulty (Easy, Medium, Hard).
-   **2 Player**: Play against a friend on the same computer.
-   **Tutorial**: Practice specific checkmate scenarios (Mate in 1, Mate in 2).
-   **Spectator**: Watch two AIs play against each other.
-   **Theme Selector**: Cycle through different board themes (Classic, Green, Blue, Wood, Dark).

### In-Game Controls
-   **Click to Select/Move**: Click a piece to see its legal moves, then click a valid destination square to move it.
-   **Undo**: Revert the last move.
-   **Reset**: Start a new game.
-   **Save/Load**: Save the current game state or load a previously saved game.
-   **Pause/Resume**: Pause the game timer and actions.
-   **Flip Board**: Change the board orientation.
-   **Resign**: Forfeit the game.
-   **Hint (AI/2 Player modes)**: Get a suggestion for the best next move.

### Game Endings
-   **Checkmate**: One player's King is under attack and has no legal moves to escape.
-   **Stalemate**: A player has no legal moves, but their King is not under attack. The game is a draw.
-   **Material Draw**: Insufficient material remains on the board to force a checkmate (e.g., King vs. King, King and Knight vs. King).
-   **Timeout**: A player runs out of time on the clock.
-   **Resignation**: A player chooses to forfeit.





1. **board/**: 
      - `chessboard.py`: Defines the `board` class which initializes the 8x8 grid of `Tile` objects and places pieces in their starting positions.
      - `move.py`: Contains the `move` class responsible for game logic, including move validation, check/checkmate detection, and handling special moves like castling and en passant.
      - `tile.py`: Defines the `Tile` class, representing a single square on the board which may contain a piece.

2. **chessart/**: Contains the PNG images for chess pieces and UI elements (e.g., highlight squares).

3. **pieces/**: Contains individual classes for each chess piece (King, Queen, Rook, Bishop, Knight, Pawn) and a `NullPiece` class for empty squares. Each class defines its specific movement rules.

4. **player/**:
      - `AI.py`: Implements the AI logic using the Minimax algorithm with Alpha-Beta pruning. It includes an evaluation function that considers material value and positional factors (Piece-Square Tables).

5.  **playchess.py**: The main entry point of the application. It initializes the Pygame window, handles user input, manages the game loop for different modes, and renders the GUI.

## Screenshots:

1. **Main Menu**: 
   <img src="project_img/main_menu.png" alt="Main Menu classics" width="600"/>

2. **Difficulty Selection**:
   <img src="project_img/difficulty_selection.png" alt="Difficulty Selection" width="600"/>

3. **2 Player Gameplay**:
   <img src="project_img/2_player_gameplay.png" alt="2 Player Gameplay white side" width="600"/>
   <img src="project_img/2_player_gameplay1.png" alt="2 Player Gameplay black side" width="600"/>
   <img src="project_img/2_player_gameplay2.png" alt="2 Player Gameplay black side Draw" width="600"/>

4. **AI Gameplay**:
   <img src="project_img/ai_gameplay.png" alt="AI Gameplay" width="600"/>

5. **Tutorial Mode**:
   <img src="project_img/tutorial_mode.png" alt="Tutorial Mode Failed" width="600"/>
   <img src="project_img/tutorial_mode1.png" alt="Tutorial Mode Completed" width="600"/>

6. **Spectator Mode**:
   <img src="project_img/spectator_mode.png" alt="Spectator Mode" width="600"/>

7. **Move Guidance & Highlights**:
   <img src="project_img/vs_theme.png" alt="Move Guidance" width="600"/>

8. **Theme Selector**:
   <img src="project_img/vs_mate.png" alt="Theme Selector Black" width="600"/>
   <img src="project_img/vs_theme.png" alt="Theme Selector Wood" width="600"/>

9. **Game Over Popup**:
   <img src="project_img/vs_mate.png" alt="Game Over" width="600"/>

10. **Save/Load & Options**:
    <img src="project_img/vs_theme.png" alt="Options" width="600"/>

## Improvements
The AI evaluation function currently uses material balance and piece-square tables. It could be further improved by incorporating more advanced positional understanding (e.g., pawn structure, king safety, mobility). Deep learning models could also be integrated for more human-like play.

## Download & Play (Pre-built Executables)

For users who want to play the game without installing Python or its dependencies, pre-built executables are available for Windows (and potentially other operating systems if built).

1.  **Go to the Releases page of this repository.**
2.  Download the latest executable for your operating system (e.g., `ChessMasterAI-Windows.exe`).
3.  Run the executable directly.

*(Note: If you encounter any security warnings, it's because the executable is not signed. You can usually bypass this by selecting "More info" or "Run anyway".)*

## Building Executables (for Distribution)

To create a standalone executable that users can run without installing Python or dependencies, you can use `PyInstaller`.

1.  **Install PyInstaller:**
    ```bash
    pip install pyinstaller
    ```
2.  **Build the executable:**
    ```bash
    pyinstaller --onefile --windowed --add-data "chessart;chessart" --add-data "pieces;pieces" --icon "icon.ico" playchess.py
    ```
    (Adjust `--add-data` paths if your asset structure is different. The format is `source;destination_folder_in_bundle`).

    The executable will be found in the `dist/` folder.

## How to Run the Application
1. Clone the repository:
   ```bash
   git clone https://github.com/pongpong-zigzag/Chess-game-AI.git
   cd Chess-game-AI
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the game:
   ```bash
   python playchess.py
   ```
