import copy
import math

# Import your existing board, tile, piece, and AI modules
from board.chessboard import board
from board.tile import Tile
from board.move import move
from pieces.nullpiece import nullpiece
from pieces.queen import queen
from pieces.rook import rook
from pieces.knight import knight
from pieces.bishop import bishop
from pieces.king import king
from pieces.pawn import pawn
from player.AI import AI

class ChessGame:
    """
    Encapsulates all the core chess game logic, board state, and rules.
    This class should be completely independent of any UI (Pygame, web, etc.).
    """
    def __init__(self):
        self.board = board()
        self.board.createboard()
        self.move_validator = move() # Your existing move validation logic
        self.ai_player = AI() # Your existing AI

        self.turn = 0 # 0 for White, 1 for Black, increments with each move
        self.enpassant_target_square = [] # [row, col] of pawn that can be captured en passant
        self.promotion_pending = False # Flag if a pawn has reached promotion rank
        self.promotion_details = {} # Stores details for promotion (e.g., pawn's original pos, new pos)
        self.last_move = [] # Stores the last move made: [[start_row, start_col], [end_row, end_col]]
        self.move_log = [] # List of move strings (e.g., "e2 to e4")
        self.history = [] # List of (game_state, turn, white_time, black_time, enpassant, last_move, move_log) tuples for undo

        self.white_time = 600 # Initial time in seconds
        self.black_time = 600
        self.game_over_status = None # None, 'white_wins', 'black_wins', 'draw', 'timeout_w', 'timeout_b', 'resigned_w', 'resigned_b'
        self.ai_depth = 3 # Default AI depth
        self.puzzle_mode = False
        self.puzzle_moves_limit = 0
        self.moves_made_count = 0

    def reset_game(self):
        """Resets the game to its initial state."""
        self.board = board()
        self.board.createboard()
        self.turn = 0
        self.enpassant_target_square = []
        self.promotion_pending = False
        self.promotion_details = {}
        self.last_move = []
        self.move_log = []
        self.history = []
        self.white_time = 600
        self.black_time = 600
        self.game_over_status = None
        self.puzzle_mode = False
        self.puzzle_moves_limit = 0
        self.moves_made_count = 0

    def save_state(self):
        """Returns a serializable dictionary of the current game state."""
        state = {
            'tiles': self.board.gameTiles, # Note: Tiles and Pieces must be serializable
            'turn': self.turn,
            'white_time': self.white_time,
            'black_time': self.black_time,
            'enpassant_target_square': self.enpassant_target_square,
            'last_move': self.last_move,
            'move_log': self.move_log,
            'history': self.history, # History also contains game states
            'ai_depth': self.ai_depth,
            'puzzle_mode': self.puzzle_mode,
            'puzzle_moves_limit': self.puzzle_moves_limit,
            'moves_made_count': self.moves_made_count,
            'game_over_status': self.game_over_status
        }
        return state

    def load_state(self, state):
        """Loads game state from a dictionary."""
        self.board.gameTiles = state['tiles']
        self.turn = state['turn']
        self.white_time = state['white_time']
        self.black_time = state['black_time']
        self.enpassant_target_square = state['enpassant_target_square']
        self.last_move = state['last_move']
        self.move_log = state['move_log']
        self.history = state['history']
        self.ai_depth = state.get('ai_depth', 3) # Use .get for backward compatibility
        self.puzzle_mode = state.get('puzzle_mode', False)
        self.puzzle_moves_limit = state.get('puzzle_moves_limit', 0)
        self.moves_made_count = state.get('moves_made_count', 0)
        self.game_over_status = state.get('game_over_status', None)

    def get_current_player_alliance(self):
        return 'White' if self.turn % 2 == 0 else 'Black'

    def get_notation(self, row, col):
        files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        return f"{files[col]}{8-row}"

    def get_legal_moves_for_piece(self, row, col):
        """
        Returns a list of legal moves for the piece at (row, col),
        considering checks and pins.
        """
        piece = self.board.gameTiles[row][col].pieceonTile
        if piece.tostring() == '-':
            return []

        moves = piece.legalmoveb(self.board.gameTiles) # Base moves

        # Add special moves (castling, en passant)
        if piece.tostring() == 'K' and piece.alliance == 'White':
            castling_moves = self.move_validator.castlingb(self.board.gameTiles) # Your castling logic
            if 'ks' in castling_moves: moves.append([0, 6])
            if 'qs' in castling_moves: moves.append([0, 2])
        elif piece.tostring() == 'k' and piece.alliance == 'Black':
            castling_moves = self.move_validator.castlingw(self.board.gameTiles) # Your castling logic
            if 'ks' in castling_moves: moves.append([7, 6])
            if 'qs' in castling_moves: moves.append([7, 2])

        if piece.tostring() == 'P' and piece.alliance == 'White':
            enpassant_moves = self.move_validator.enpassantb(self.board.gameTiles, row, col)
            if enpassant_moves:
                if enpassant_moves[1] == 'r': moves.append([row + 1, col + 1])
                else: moves.append([row + 1, col - 1])
        elif piece.tostring() == 'p' and piece.alliance == 'Black':
            enpassant_moves = self.move_validator.enpassantb(self.board.gameTiles, row, col)
            if enpassant_moves:
                if enpassant_moves[1] == 'r': moves.append([row - 1, col + 1])
                else: moves.append([row - 1, col - 1])

        # Filter moves based on checks and pins
        if piece.alliance == 'White':
            moves = self.move_validator.pinnedw(self.board.gameTiles, moves, row, col)
        else: # Black
            moves = self.move_validator.pinnedb(self.board.gameTiles, moves, row, col)

        # Ensure only current player's pieces can be moved
        if (self.turn % 2 == 0 and piece.alliance == 'Black') or \
           (self.turn % 2 == 1 and piece.alliance == 'White'):
            return []

        return moves

    def apply_move(self, start_row, start_col, end_row, end_col):
        """
        Applies a move to the board and updates game state.
        Returns True if move was successful, False otherwise.
        """
        piece = self.board.gameTiles[start_row][start_col].pieceonTile
        if piece.tostring() == '-':
            return False # No piece to move

        # Check if the move is legal
        legal_moves = self.get_legal_moves_for_piece(start_row, start_col)
        if [end_row, end_col] not in legal_moves:
            return False

        # Store current state for undo
        self.history.append((
            copy.deepcopy(self.board.gameTiles),
            self.turn,
            self.white_time,
            self.black_time,
            copy.deepcopy(self.enpassant_target_square),
            copy.deepcopy(self.last_move),
            copy.deepcopy(self.move_log)
        ))

        is_capture = (self.board.gameTiles[end_row][end_col].pieceonTile.tostring() != '-')

        # Handle special moves and update piece properties
        if piece.tostring() in ['K', 'R', 'k', 'r']:
            piece.moved = True

        # Castling
        if piece.tostring() == 'K' and abs(start_col - end_col) == 2: # White King castling
            rook_col = 7 if end_col == 6 else 0
            new_rook_col = 5 if end_col == 6 else 3
            rook_piece = self.board.gameTiles[start_row][rook_col].pieceonTile
            self.board.gameTiles[start_row][new_rook_col] = Tile(self._update_pos(start_row, new_rook_col), rook_piece)
            self.board.gameTiles[start_row][rook_col] = Tile(self._update_pos(start_row, rook_col), nullpiece())
            rook_piece.position = self._update_pos(start_row, new_rook_col)
        elif piece.tostring() == 'k' and abs(start_col - end_col) == 2: # Black King castling
            rook_col = 7 if end_col == 6 else 0
            new_rook_col = 5 if end_col == 6 else 3
            rook_piece = self.board.gameTiles[start_row][rook_col].pieceonTile
            self.board.gameTiles[start_row][new_rook_col] = Tile(self._update_pos(start_row, new_rook_col), rook_piece)
            self.board.gameTiles[start_row][rook_col] = Tile(self._update_pos(start_row, rook_col), nullpiece())
            rook_piece.position = self._update_pos(start_row, new_rook_col)

        # En Passant Capture
        if piece.tostring() in ['P', 'p'] and end_col != start_col and \
           self.board.gameTiles[end_row][end_col].pieceonTile.tostring() == '-':
            # This is an en passant capture
            is_capture = True
            if piece.alliance == 'White':
                self.board.gameTiles[end_row + 1][end_col] = Tile(self._update_pos(end_row + 1, end_col), nullpiece())
            else:
                self.board.gameTiles[end_row - 1][end_col] = Tile(self._update_pos(end_row - 1, end_col), nullpiece())

        # Clear previous en passant target
        if self.enpassant_target_square:
            pawn_tile = self.board.gameTiles[self.enpassant_target_square[0]][self.enpassant_target_square[1]].pieceonTile
            if pawn_tile.tostring() in ['P', 'p']:
                pawn_tile.enpassant = False
        self.enpassant_target_square = []

        # Set new en passant target if pawn moves two squares
        if piece.tostring() in ['P', 'p'] and abs(start_row - end_row) == 2:
            piece.enpassant = True
            self.enpassant_target_square = [end_row, end_col]

        # Move the piece
        self.board.gameTiles[end_row][end_col] = Tile(self._update_pos(end_row, end_col), piece)
        self.board.gameTiles[start_row][start_col] = Tile(self._update_pos(start_row, start_col), nullpiece())
        piece.position = self._update_pos(end_row, end_col)

        # Check for Pawn Promotion
        if (piece.tostring() == 'P' and end_row == 7) or \
           (piece.tostring() == 'p' and end_row == 0):
            self.promotion_pending = True
            self.promotion_details = {'row': end_row, 'col': end_col, 'alliance': piece.alliance}
        else:
            self.promotion_pending = False

        self.last_move = [[start_row, start_col], [end_row, end_col]]
        self.move_log.append(f"{self.get_notation(start_row, start_col)} to {self.get_notation(end_row, end_col)}")
        self.turn += 1
        self.moves_made_count += 1

        self.check_game_over() # Update game over status after each move
        return True, is_capture

    def promote_pawn(self, row, col, piece_type_char):
        """Promotes a pawn at (row, col) to the given piece type."""
        if not self.promotion_pending or \
           self.promotion_details['row'] != row or \
           self.promotion_details['col'] != col:
            return False

        alliance = self.promotion_details['alliance']
        new_piece = None
        pos = self._update_pos(row, col)

        if piece_type_char.upper() == 'Q': new_piece = queen(alliance, pos)
        elif piece_type_char.upper() == 'R': new_piece = rook(alliance, pos)
        elif piece_type_char.upper() == 'N': new_piece = knight(alliance, pos)
        elif piece_type_char.upper() == 'B': new_piece = bishop(alliance, pos)

        if new_piece:
            self.board.gameTiles[row][col].pieceonTile = new_piece
            self.promotion_pending = False
            self.promotion_details = {}
            self.check_game_over() # Re-check game over status after promotion
            return True
        return False

    def undo_last_move(self):
        """Undoes the last move made."""
        if self.history:
            state = self.history.pop()
            self.board.gameTiles = copy.deepcopy(state[0])
            self.turn = state[1]
            self.white_time = state[2]
            self.black_time = state[3]
            self.enpassant_target_square = copy.deepcopy(state[4])
            self.last_move = copy.deepcopy(state[5])
            self.move_log = copy.deepcopy(state[6])
            self.promotion_pending = False
            self.promotion_details = {}
            self.game_over_status = None # Clear game over status on undo
            self.moves_made_count -= 1
            return True
        return False

    def get_ai_move(self, is_white_turn, depth=None):
        """Calculates the best AI move."""
        current_depth = depth if depth is not None else self.ai_depth
        # AI evaluate returns (start_row, start_col, end_row, end_col)
        return self.ai_player.evaluate(copy.deepcopy(self.board.gameTiles), current_depth, is_white_turn)

    def check_game_over(self):
        """
        Checks for checkmate, stalemate, and insufficient material.
        Updates self.game_over_status.
        """
        if self.game_over_status: # Already game over
            return self.game_over_status

        current_player_alliance = self.get_current_player_alliance()
        opponent_alliance = 'Black' if current_player_alliance == 'White' else 'White'

        # Check for checkmate/stalemate
        all_legal_moves = []
        for r in range(8):
            for c in range(8):
                piece = self.board.gameTiles[r][c].pieceonTile
                if piece.alliance == current_player_alliance:
                    all_legal_moves.extend(self.get_legal_moves_for_piece(r, c))

        if not all_legal_moves: # No legal moves
            if current_player_alliance == 'White':
                if self.move_validator.checkw(self.board.gameTiles)[0] == 'checked':
                    self.game_over_status = 'black_wins' # White is checkmated
                else:
                    self.game_over_status = 'draw' # White is stalemated
            else: # Black's turn
                if self.move_validator.checkb(self.board.gameTiles)[0] == 'checked':
                    self.game_over_status = 'white_wins' # Black is checkmated
                else:
                    self.game_over_status = 'draw' # Black is stalemated

        # Check for insufficient material (simplified)
        if self._check_insufficient_material(self.board.gameTiles):
            self.game_over_status = 'draw'

        return self.game_over_status

    def _check_insufficient_material(self, gametiles):
        """A simplified check for insufficient material (e.g., K vs K, K vs KN, K vs KB)."""
        piece_counts = {'K': 0, 'Q': 0, 'R': 0, 'B': 0, 'N': 0, 'P': 0,
                        'k': 0, 'q': 0, 'r': 0, 'b': 0, 'n': 0, 'p': 0}
        for r in range(8):
            for c in range(8):
                piece_char = gametiles[r][c].pieceonTile.tostring()
                if piece_char != '-':
                    piece_counts[piece_char] += 1

        total_pieces = sum(piece_counts.values())

        if total_pieces == 2: # King vs King
            return True
        if total_pieces == 3: # King vs King and one minor piece
            if (piece_counts['N'] == 1 or piece_counts['B'] == 1 or
                piece_counts['n'] == 1 or piece_counts['b'] == 1):
                return True
        # More complex insufficient material checks can be added here
        return False

    def _update_pos(self, row, col):
        """Helper to calculate 1D position from 2D coordinates."""
        return row * 8 + col

    def setup_puzzle(self, puzzle_type):
        """Sets up a specific chess puzzle."""
        self.reset_game()
        self.puzzle_mode = True

        # Clear board
        for r in range(8):
            for c in range(8):
                self.board.gameTiles[r][c] = Tile(r*8+c, nullpiece())

        if puzzle_type == 1: # Mate in 1
            self.puzzle_moves_limit = 1
            self.board.gameTiles[2][1] = Tile(17, king("White", 17)) # King at b6
            self.board.gameTiles[7][7] = Tile(63, rook("White", 63)) # Rook at h1
            self.board.gameTiles[0][0] = Tile(0, king("Black", 0))   # King at a8
            self.turn = 0 # White to move

        elif puzzle_type == 2: # Mate in 2
            self.puzzle_moves_limit = 2
            self.board.gameTiles[2][5] = Tile(21, king("White", 21)) # King at f6
            self.board.gameTiles[7][0] = Tile(56, rook("White", 56)) # Rook at a1
            self.board.gameTiles[0][7] = Tile(7, king("Black", 7))   # King at h8
            self.turn = 0 # White to move

        # You'll need to add more puzzles here

    def get_board_state_for_display(self):
        """Returns the current board state in a format suitable for UI rendering."""
        # This could return a list of (piece_char, alliance, row, col) tuples
        # or simply the gameTiles 2D array if the UI can interpret it.
        return self.board.gameTiles

    def get_move_log(self):
        return self.move_log

    def get_last_move(self):
        return self.last_move

    def get_times(self):
        return self.white_time, self.black_time

    def update_time(self, delta_seconds):
        if self.turn % 2 == 0:
            self.white_time -= delta_seconds
            if self.white_time <= 0:
                self.game_over_status = 'timeout_w'
        else:
            self.black_time -= delta_seconds
            if self.black_time <= 0:
                self.game_over_status = 'timeout_b'

    def resign(self, alliance):
        if alliance == 'White':
            self.game_over_status = 'resigned_w'
        else:
            self.game_over_status = 'resigned_b'