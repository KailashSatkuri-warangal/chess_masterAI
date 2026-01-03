import pygame
import asyncio
import js # Pyodide's JavaScript bridge
import math
import json # For saving/loading state to localStorage

# Import your refactored game logic
from game_engine.chess_game_logic import ChessGame

# --- UI Constants (from playchess.py) ---
BACKGROUND_COLOR = (49, 46, 43)
BUTTON_COLOR = (118, 150, 86)
TEXT_COLOR = (255, 255, 255)

THEMES = [
    ((240, 217, 181), (181, 136, 99), "Classic"),
    ((238, 238, 210), (118, 150, 86), "Green"),
    ((232, 235, 239), (125, 135, 150), "Blue"),
    ((210, 180, 140), (139, 69, 19), "Wood"),
    ((140, 140, 140), (80, 80, 80), "Dark")
]
current_theme_idx = 0
BOARD_WHITE = THEMES[current_theme_idx][0]
BOARD_BLACK = THEMES[current_theme_idx][1]
HIGHLIGHT_COLOR = (186, 202, 68)
HINT_COLOR = (100, 200, 255)

SQUARE_SIZE = 100
BOARD_WIDTH = 8 * SQUARE_SIZE
BOARD_HEIGHT = 8 * SQUARE_SIZE
SIDEBAR_WIDTH = 200
TOTAL_WIDTH = BOARD_WIDTH + SIDEBAR_WIDTH
TOTAL_HEIGHT = BOARD_HEIGHT

class WebGameUI:
    def __init__(self, game_instance: ChessGame):
        self.game = game_instance
        self.screen = None # Will be initialized by Pygame.display.set_mode
        self.clock = pygame.time.Clock()

        self.piece_images = {}
        self.move_sound = None
        self.capture_sound = None
        self.red_square_img = None

        self.font = None
        self.font_small = None

        self.flipped = False
        self.paused = False
        self.selected_piece_pos = None # [row, col]
        self.highlighted_moves = [] # List of [row, col]
        self.hint_move = [] # List of [[start_row, start_col], [end_row, end_col]]

        self.menu_state = 'main' # 'main', 'difficulty', 'tutorial_menu', 'game'
        self.game_mode = None # '2player', 'ai', 'tutorial', 'spectator'

        self.load_assets_task = asyncio.create_task(self._load_all_assets())

        # Attach event listener to the canvas element
        # Pygame-ce automatically creates a canvas. We need to get a reference to it.
        # The canvas is usually the first canvas element in the document.
        self.canvas = js.document.getElementsByTagName("canvas")[0]
        if self.canvas:
            self.canvas.addEventListener("click", self._handle_canvas_click)
            self.canvas.addEventListener("mousemove", self._handle_canvas_mousemove) # For hover effects if needed
        else:
            print("Error: Pygame canvas not found in DOM.")

    async def _load_all_assets(self):
        """Loads all images and sounds asynchronously."""
        print("Loading assets...")
        # Fonts
        # Pygame-ce in Pyodide might have issues with local font files.
        # Using default font or a web-safe font is often easier.
        try:
            self.font = pygame.font.Font('freesansbold.ttf', 32)
            self.font_small = pygame.font.Font('freesansbold.ttf', 20)
        except Exception as e:
            print(f"Warning: Could not load custom font, using default. {e}")
            self.font = pygame.font.SysFont(None, 32)
            self.font_small = pygame.font.SysFont(None, 20)

        # Piece Images
        for piece_char in ['B', 'W']: # Alliance
            for piece_type in ['Q', 'R', 'N', 'B', 'K', 'P']: # Piece type
                key = piece_char + piece_type
                path = f"chessart/{key}.png"
                try:
                    # Pygame-ce's image.load should work with relative paths if assets are served
                    img = pygame.image.load(path)
                    self.piece_images[key] = pygame.transform.scale(img, (SQUARE_SIZE, SQUARE_SIZE))
                except pygame.error as e:
                    print(f"Error loading image {path}: {e}")
                    self.piece_images[key] = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE)) # Dummy surface

        # Red Square for highlights
        try:
            self.red_square_img = pygame.image.load("chessart/red_square.png")
            self.red_square_img = pygame.transform.scale(self.red_square_img, (SQUARE_SIZE, SQUARE_SIZE))
        except pygame.error as e:
            print(f"Error loading red_square.png: {e}")
            self.red_square_img = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
            self.red_square_img.fill((255, 0, 0, 100)) # Semi-transparent red

        # Sound Effects
        try:
            self.move_sound = pygame.mixer.Sound('pieces/move.wav')
            self.capture_sound = pygame.mixer.Sound('pieces/capture.wav')
        except pygame.error as e:
            print(f"Warning: Sound files not found or failed to load. {e}")
            class DummySound:
                def play(self): pass
            self.move_sound = DummySound()
            self.capture_sound = DummySound()
        print("Assets loaded.")

    def _handle_canvas_click(self, event):
        """Handles click events on the Pygame canvas."""
        # Get mouse coordinates relative to the canvas
        rect = self.canvas.getBoundingClientRect()
        mouse_x = event.clientX - rect.left
        mouse_y = event.clientY - rect.top

        # Post a Pygame MOUSEBUTTONDOWN event
        pygame_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(mouse_x, mouse_y))
        pygame.event.post(pygame_event)

    def _handle_canvas_mousemove(self, event):
        """Handles mouse move events on the Pygame canvas (for hover effects)."""
        # Get mouse coordinates relative to the canvas
        rect = self.canvas.getBoundingClientRect()
        mouse_x = event.clientX - rect.left
        mouse_y = event.clientY - rect.top
        
        # Post a Pygame MOUSEMOTION event
        pygame_event = pygame.event.Event(pygame.MOUSEMOTION, pos=(mouse_x, mouse_y))
        pygame.event.post(pygame_event)

    def _get_board_coords(self, mouse_x, mouse_y):
        """Converts pixel coordinates to board (row, col) coordinates."""
        if mouse_x >= BOARD_WIDTH or mouse_y >= BOARD_HEIGHT:
            return None, None # Clicked outside the board area

        col = math.floor(mouse_x / SQUARE_SIZE)
        row = math.floor(mouse_y / SQUARE_SIZE)

        if self.flipped:
            col = 7 - col
            row = 7 - row
        return row, col

    def _get_pixel_coords(self, row, col):
        """Converts board (row, col) coordinates to pixel coordinates."""
        if self.flipped:
            col = 7 - col
            row = 7 - row
        return col * SQUARE_SIZE, row * SQUARE_SIZE

    def draw_board(self):
        """Draws the chess board and pieces."""
        board_state = self.game.get_board_state_for_display()
        
        for r in range(8):
            for c in range(8):
                display_r, display_c = (7 - r, 7 - c) if self.flipped else (r, c)
                
                # Determine square color
                if [r, c] in self.game.get_last_move(): # Last move highlight
                    sq_color = HIGHLIGHT_COLOR
                elif (r + c) % 2 == 0:
                    sq_color = BOARD_WHITE
                else:
                    sq_color = BOARD_BLACK
                
                pygame.draw.rect(self.screen, sq_color, (display_c * SQUARE_SIZE, display_r * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

                # Draw piece
                piece = board_state[r][c].pieceonTile
                if piece.tostring() != '-':
                    piece_key = piece.alliance[0].upper() + piece.tostring().upper()
                    img = self.piece_images.get(piece_key)
                    if img:
                        self.screen.blit(img, (display_c * SQUARE_SIZE, display_r * SQUARE_SIZE))

        # Draw highlighted legal moves
        for move_pos in self.highlighted_moves:
            display_r, display_c = (7 - move_pos[0], 7 - move_pos[1]) if self.flipped else (move_pos[0], move_pos[1])
            # Draw a semi-transparent red square or a dot
            self.screen.blit(self.red_square_img, (display_c * SQUARE_SIZE, display_r * SQUARE_SIZE))

        # Draw hint move
        if self.hint_move:
            for h_sq in self.hint_move:
                display_r, display_c = (7 - h_sq[0], 7 - h_sq[1]) if self.flipped else (h_sq[0], h_sq[1])
                pygame.draw.rect(self.screen, HINT_COLOR, (display_c * SQUARE_SIZE, display_r * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 5)

        # Draw selected piece (if any)
        if self.selected_piece_pos:
            r, c = self.selected_piece_pos
            display_r, display_c = (7 - r, 7 - c) if self.flipped else (r, c)
            pygame.draw.rect(self.screen, HIGHLIGHT_COLOR, (display_c * SQUARE_SIZE, display_r * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 3)

    def draw_sidebar(self):
        """Draws the sidebar with timers, move log, and buttons."""
        sidebar_x = BOARD_WIDTH
        self.screen.fill(BACKGROUND_COLOR, (sidebar_x, 0, SIDEBAR_WIDTH, TOTAL_HEIGHT))

        # Draw Timers
        white_time, black_time = self.game.get_times()
        b_text = self.font.render(f"Black: {self._format_time(black_time)}", True, TEXT_COLOR)
        w_text = self.font.render(f"White: {self._format_time(white_time)}", True, TEXT_COLOR)
        self.screen.blit(b_text, (sidebar_x + 10, 50))
        self.screen.blit(w_text, (sidebar_x + 10, TOTAL_HEIGHT - 100))

        # Draw Move Log
        title = self.font_small.render("Move Log:", True, TEXT_COLOR)
        self.screen.blit(title, (sidebar_x + 10, 100))
        move_log = self.game.get_move_log()
        start_index = max(0, len(move_log) - 6) # Show last 6 moves
        for i in range(start_index, len(move_log)):
            text_str = f"{i+1}. {move_log[i]}"
            text_render = self.font_small.render(text_str, True, TEXT_COLOR)
            self.screen.blit(text_render, (sidebar_x + 10, 130 + (i - start_index) * 20))

        # Draw Buttons
        self._draw_button(sidebar_x + 10, 180, 180, 50, 'Flip Board', self.font, self.flipped)
        self._draw_button(sidebar_x + 10, 250, 180, 50, 'Resume' if self.paused else 'Pause', self.font, self.paused)
        self._draw_button(sidebar_x + 10, 350, 180, 50, 'Undo', self.font)
        self._draw_button(sidebar_x + 10, 450, 180, 50, 'Reset', self.font)
        self._draw_button(sidebar_x + 10, 550, 180, 50, 'Save', self.font)
        self._draw_button(sidebar_x + 10, 650, 180, 50, 'Load', self.font)
        self._draw_button(sidebar_x + 10, 740, 180, 50, 'Resign', self.font)
        
        # Hint button only in AI/2Player modes
        if self.game_mode in ['ai', '2player', 'tutorial']:
            self._draw_button(sidebar_x + 10, 80, 180, 40, 'Hint', self.font_small)

    def _draw_button(self, x, y, w, h, text_str, font_obj, is_active=False):
        """Helper to draw a button."""
        color = HIGHLIGHT_COLOR if is_active else BUTTON_COLOR
        pygame.draw.rect(self.screen, color, (x, y, w, h))
        text_render = font_obj.render(text_str, True, TEXT_COLOR)
        text_rect = text_render.get_rect(center=(x + w // 2, y + h // 2))
        self.screen.blit(text_render, text_rect)

    def _format_time(self, seconds):
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02}:{secs:02}"

    def draw_popup(self, text_surface, show_play_again=True):
        """Draws a popup message."""
        # Draw Popup Box
        pygame.draw.rect(self.screen, BACKGROUND_COLOR, [200, 300, 600, 200])
        pygame.draw.rect(self.screen, HIGHLIGHT_COLOR, [200, 300, 600, 200], 5)
        # Center Text
        text_rect = text_surface.get_rect(center=(500, 360))
        self.screen.blit(text_surface, text_rect)
        
        if show_play_again:
            # Draw Play Again Button
            pygame.draw.rect(self.screen, BUTTON_COLOR, [425, 410, 150, 50])
            text_restart = self.font_small.render('Play Again', True, TEXT_COLOR)
            text_rect_restart = text_restart.get_rect(center=(500, 435))
            self.screen.blit(text_restart, text_rect_restart)

    def _handle_main_menu_click(self, mouse_pos):
        """Handles clicks in the main menu."""
        x, y = mouse_pos
        if 200 <= x <= 400 and 300 <= y <= 400: # AI Mode
            self.menu_state = 'difficulty'
        elif 600 <= x <= 800 and 300 <= y <= 400: # 2 Player
            self.game_mode = '2player'
            self.menu_state = 'game'
            self.game.reset_game()
        elif 400 <= x <= 600 and 500 <= y <= 580: # Tutorial
            self.menu_state = 'tutorial_menu'
        elif 400 <= x <= 600 and 400 <= y <= 480: # Spectator
            self.game_mode = 'spectator'
            self.menu_state = 'game'
            self.game.reset_game()
        elif 400 <= x <= 600 and 600 <= y <= 680: # Theme Selector
            global current_theme_idx, BOARD_WHITE, BOARD_BLACK
            current_theme_idx = (current_theme_idx + 1) % len(THEMES)
            BOARD_WHITE = THEMES[current_theme_idx][0]
            BOARD_BLACK = THEMES[current_theme_idx][1]

    def _handle_difficulty_menu_click(self, mouse_pos):
        """Handles clicks in the difficulty selection menu."""
        x, y = mouse_pos
        if 400 <= x <= 600:
            if 250 <= y <= 330: self.game.ai_depth = 1; self.game_mode = 'ai'; self.menu_state = 'game'; self.game.reset_game()
            elif 350 <= y <= 430: self.game.ai_depth = 2; self.game_mode = 'ai'; self.menu_state = 'game'; self.game.reset_game()
            elif 450 <= y <= 530: self.game.ai_depth = 3; self.game_mode = 'ai'; self.menu_state = 'game'; self.game.reset_game()

    def _handle_tutorial_menu_click(self, mouse_pos):
        """Handles clicks in the tutorial selection menu."""
        x, y = mouse_pos
        if 400 <= x <= 600:
            if 250 <= y <= 330: self.game.setup_puzzle(1); self.game_mode = 'tutorial'; self.menu_state = 'game'
            elif 350 <= y <= 430: self.game.setup_puzzle(2); self.game_mode = 'tutorial'; self.menu_state = 'game'

    def _handle_game_click(self, mouse_pos):
        """Handles clicks during active gameplay."""
        x, y = mouse_pos
        
        # Sidebar button clicks
        if x >= BOARD_WIDTH:
            if 180 <= y <= 230: self.flipped = not self.flipped # Flip Board
            elif 250 <= y <= 300: self.paused = not self.paused # Pause/Resume
            elif 350 <= y <= 400: self.game.undo_last_move(); self.selected_piece_pos = None; self.highlighted_moves = []; self.hint_move = [] # Undo
            elif 450 <= y <= 500: self.game.reset_game(); self.selected_piece_pos = None; self.highlighted_moves = []; self.hint_move = [] # Reset
            elif 550 <= y <= 600: self._save_game_to_localstorage() # Save
            elif 650 <= y <= 700: self._load_game_from_localstorage() # Load
            elif 740 <= y <= 790: self.game.resign(self.game.get_current_player_alliance()); self.menu_state = 'game_over' # Resign
            elif 80 <= y <= 120 and self.game_mode in ['ai', '2player', 'tutorial']: # Hint
                is_white = (self.game.turn % 2 == 0)
                # Use a lower depth for hints to be quick
                hy, hx, hfx, hfy = self.game.get_ai_move(is_white, depth=2)
                self.hint_move = [[hy, hx], [hfx, hfy]]
            return

        # If paused, only sidebar buttons work
        if self.paused:
            return

        # Board clicks
        row, col = self._get_board_coords(x, y)
        if row is None or col is None:
            return

        # Handle Pawn Promotion selection
        if self.game.promotion_pending:
            # This part needs custom UI for promotion selection.
            # For simplicity, we'll auto-promote to Queen for now.
            # In a real game, you'd draw 4 squares for Q, R, N, B and let user click.
            # For now, just complete the promotion.
            if self.game.promote_pawn(self.game.promotion_details['row'], self.game.promotion_details['col'], 'Q'):
                self.move_sound.play() # Play sound for promotion
                self.selected_piece_pos = None
                self.highlighted_moves = []
            return

        # If a piece is already selected
        if self.selected_piece_pos:
            start_r, start_c = self.selected_piece_pos
            # Check if clicked on a valid move target
            if [row, col] in self.highlighted_moves:
                success, is_capture = self.game.apply_move(start_r, start_c, row, col)
                if success:
                    if is_capture: self.capture_sound.play()
                    else: self.move_sound.play()
                    self.selected_piece_pos = None
                    self.highlighted_moves = []
                    self.hint_move = [] # Clear hint after move
            else:
                # Clicked elsewhere, deselect
                self.selected_piece_pos = None
                self.highlighted_moves = []
                # If clicked on another piece of current player, select it
                piece = self.game.board.gameTiles[row][col].pieceonTile
                if piece.alliance == self.game.get_current_player_alliance():
                    self.selected_piece_pos = [row, col]
                    self.highlighted_moves = self.game.get_legal_moves_for_piece(row, col)
        else:
            # No piece selected, try to select one
            piece = self.game.board.gameTiles[row][col].pieceonTile
            if piece.alliance == self.game.get_current_player_alliance():
                self.selected_piece_pos = [row, col]
                self.highlighted_moves = self.game.get_legal_moves_for_piece(row, col)

    def _save_game_to_localstorage(self):
        """Saves the current game state to browser's localStorage."""
        try:
            state = self.game.save_state()
            # Convert complex objects (like Tile, Piece instances) to a serializable format
            # This requires custom serialization for your board/piece objects.
            # For a quick demo, we'll try to serialize directly, but this might fail
            # if your objects are not JSON-serializable.
            # A robust solution would involve converting gameTiles to a list of dicts.
            serializable_state = self._serialize_game_state(state)
            js.localStorage.setItem('chess_savegame', json.dumps(serializable_state))
            print("Game saved to localStorage.")
        except Exception as e:
            print(f"Error saving game: {e}")

    def _load_game_from_localstorage(self):
        """Loads game state from browser's localStorage."""
        try:
            saved_data = js.localStorage.getItem('chess_savegame')
            if saved_data:
                state_dict = json.loads(saved_data)
                # Convert back from serializable format to game objects
                loaded_state = self._deserialize_game_state(state_dict)
                self.game.load_state(loaded_state)
                self.selected_piece_pos = None
                self.highlighted_moves = []
                self.hint_move = []
                self.paused = False
                print("Game loaded from localStorage.")
            else:
                print("No saved game found in localStorage.")
        except Exception as e:
            print(f"Error loading game: {e}")

    def _serialize_game_state(self, state):
        """Converts game state objects into JSON-serializable data."""
        serializable_state = copy.deepcopy(state)
        # Convert gameTiles (2D array of Tile objects)
        serializable_state['tiles'] = [
            [
                {'pos': tile.position, 'piece': self._serialize_piece(tile.pieceonTile)}
                for tile in row
            ]
            for row in state['tiles']
        ]
        # Convert history (list of tuples, each containing gameTiles)
        serializable_history = []
        for hist_entry in state['history']:
            hist_tiles = [
                [
                    {'pos': tile.position, 'piece': self._serialize_piece(tile.pieceonTile)}
                    for tile in row
                ]
                for row in hist_entry[0]
            ]
            serializable_history.append((hist_tiles, hist_entry[1], hist_entry[2], hist_entry[3], hist_entry[4], hist_entry[5], hist_entry[6]))
        serializable_state['history'] = serializable_history
        return serializable_state

    def _deserialize_game_state(self, serializable_state):
        """Converts JSON-serializable data back into game state objects."""
        deserialized_state = copy.deepcopy(serializable_state)
        # Convert tiles back to Tile objects with Piece objects
        deserialized_state['tiles'] = [
            [
                Tile(tile_data['pos'], self._deserialize_piece(tile_data['piece']))
                for tile_data in row
            ]
            for row in serializable_state['tiles']
        ]
        # Convert history back
        deserialized_history = []
        for hist_entry in serializable_state['history']:
            hist_tiles = [
                [
                    Tile(tile_data['pos'], self._deserialize_piece(tile_data['piece']))
                    for tile_data in row
                ]
                for row in hist_entry[0]
            ]
            deserialized_history.append((hist_tiles, hist_entry[1], hist_entry[2], hist_entry[3], hist_entry[4], hist_entry[5], hist_entry[6]))
        deserialized_state['history'] = deserialized_history
        return deserialized_state

    def _serialize_piece(self, piece):
        """Converts a Piece object to a serializable dictionary."""
        if piece.tostring() == '-':
            return {'type': '-', 'alliance': None, 'pos': piece.position}
        return {
            'type': piece.tostring(),
            'alliance': piece.alliance,
            'pos': piece.position,
            'moved': getattr(piece, 'moved', False), # For King/Rook
            'enpassant': getattr(piece, 'enpassant', False) # For Pawn
        }

    def _deserialize_piece(self, piece_data):
        """Converts a serializable dictionary back to a Piece object."""
        if piece_data['type'] == '-':
            return nullpiece()
        
        alliance = piece_data['alliance']
        pos = piece_data['pos']
        moved = piece_data.get('moved', False)
        enpassant = piece_data.get('enpassant', False)

        piece_map = {
            'Q': queen, 'R': rook, 'N': knight, 'B': bishop, 'K': king, 'P': pawn,
            'q': queen, 'r': rook, 'n': knight, 'b': bishop, 'k': king, 'p': pawn
        }
        piece_class = piece_map.get(piece_data['type'].upper())
        if piece_class:
            new_piece = piece_class(alliance, pos)
            if piece_data['type'].upper() in ['K', 'R']:
                new_piece.moved = moved
            if piece_data['type'].upper() == 'P':
                new_piece.enpassant = enpassant
            return new_piece
        return nullpiece() # Fallback

    async def main_loop(self):
        """The main game loop for the web UI."""
        # Wait for assets to load before starting the game loop
        await self.load_assets_task

        # Initialize Pygame display after assets are loaded
        # Pygame-ce will try to find a canvas in the DOM or create one.
        # We ensure the HTML has a canvas or container for it.
        self.screen = pygame.display.set_mode((TOTAL_WIDTH, TOTAL_HEIGHT))
        pygame.display.set_caption("Chess Master AI")

        running = True
        while running:
            dt = self.clock.get_time() / 1000.0 # Time since last frame in seconds

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    # In a web context, this might mean navigating away or closing the tab.
                    # We can't 'quit()' the browser.
                    print("Game loop requested quit.")
                    break
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.game.game_over_status: # If game is over, only "Play Again" button works
                        if 425 <= event.pos[0] <= 575 and 410 <= event.pos[1] <= 460:
                            # Simulate os.execl(sys.executable, sys.executable, *sys.argv)
                            js.window.location.reload()
                        continue

                    if self.menu_state == 'main':
                        self._handle_main_menu_click(event.pos)
                    elif self.menu_state == 'difficulty':
                        self._handle_difficulty_menu_click(event.pos)
                    elif self.menu_state == 'tutorial_menu':
                        self._handle_tutorial_menu_click(event.pos)
                    elif self.menu_state == 'game':
                        self._handle_game_click(event.pos)

            # Game logic updates (timers, AI moves)
            if self.menu_state == 'game' and not self.paused and not self.game.game_over_status:
                self.game.update_time(dt)

                if self.game.game_over_status: # Check if time ran out
                    self.menu_state = 'game_over'

                if self.game_mode == 'ai' and self.game.get_current_player_alliance() == 'Black':
                    # AI's turn
                    ai_start_r, ai_start_c, ai_end_r, ai_end_c = self.game.get_ai_move(False)
                    if ai_start_r is not None:
                        success, is_capture = self.game.apply_move(ai_start_r, ai_start_c, ai_end_r, ai_end_c)
                        if success:
                            if is_capture: self.capture_sound.play()
                            else: self.move_sound.play()
                            # Small delay for AI move to be visible
                            await asyncio.sleep(0.5)
                    else:
                        # AI has no legal moves (stalemate/checkmate)
                        self.game.check_game_over()
                        self.menu_state = 'game_over'

                elif self.game_mode == 'spectator':
                    # Both AIs play
                    current_alliance = self.game.get_current_player_alliance()
                    ai_start_r, ai_start_c, ai_end_r, ai_end_c = self.game.get_ai_move(current_alliance == 'White')
                    if ai_start_r is not None:
                        success, is_capture = self.game.apply_move(ai_start_r, ai_start_c, ai_end_r, ai_end_c)
                        if success:
                            if is_capture: self.capture_sound.play()
                            else: self.move_sound.play()
                            await asyncio.sleep(0.5)
                    else:
                        self.game.check_game_over()
                        self.menu_state = 'game_over'

                elif self.game_mode == 'tutorial' and self.game.get_current_player_alliance() == 'Black':
                    # Tutorial AI (Black)
                    ai_start_r, ai_start_c, ai_end_r, ai_end_c = self.game.get_ai_move(False, depth=2) # Lower depth for tutorial AI
                    if ai_start_r is not None:
                        success, is_capture = self.game.apply_move(ai_start_r, ai_start_c, ai_end_r, ai_end_c)
                        if success:
                            if is_capture: self.capture_sound.play()
                            else: self.move_sound.play()
                            await asyncio.sleep(0.5)
                    else:
                        # AI has no legal moves (stalemate/checkmate)
                        self.game.check_game_over()
                        self.menu_state = 'game_over'

                # Check for game over conditions after each move
                if self.game.game_over_status:
                    self.menu_state = 'game_over'

            # Drawing
            self.screen.fill(BACKGROUND_COLOR)

            if self.menu_state == 'main':
                self._draw_main_menu()
            elif self.menu_state == 'difficulty':
                self._draw_difficulty_menu()
            elif self.menu_state == 'tutorial_menu':
                self._draw_tutorial_menu()
            elif self.menu_state == 'game':
                self.draw_board()
                self.draw_sidebar()
                if self.paused:
                    self._draw_paused_overlay()
            elif self.menu_state == 'game_over':
                self.draw_board()
                self.draw_sidebar()
                self._draw_game_over_popup()

            pygame.display.flip()
            self.clock.tick(60)

            # Yield control back to the browser event loop
            await asyncio.sleep(0)

        print("Game loop ended.")

    def _draw_main_menu(self):
        """Draws the main menu screen."""
        text_title = self.font.render('pychess', True, TEXT_COLOR)
        text_title_rect = text_title.get_rect(center=(TOTAL_WIDTH // 2, 100))
        self.screen.blit(text_title, text_title_rect)

        self._draw_button(200, 300, 200, 100, 'AI', self.font)
        self._draw_button(600, 300, 200, 100, '2 player', self.font)
        self._draw_button(400, 500, 200, 80, 'Tutorial', self.font)
        self._draw_button(400, 400, 200, 80, 'Spectator', self.font)
        
        text_theme = self.font.render(f'Theme: {THEMES[current_theme_idx][2]}', True, TEXT_COLOR)
        self_draw_button(400, 600, 200, 80, text_theme.get_text(), self.font)
        self.screen.blit(text_theme, text_theme.get_rect(center=(500, 640)))

        text_credit = self.font.render('Made by: Kailash', True, TEXT_COLOR)
        text_credit_rect = text_credit.get_rect(center=(TOTAL_WIDTH // 2, 700))
        self.screen.blit(text_credit, text_credit_rect)

    def _draw_difficulty_menu(self):
        """Draws the AI difficulty selection menu."""
        title_diff = self.font.render('Select Difficulty', True, TEXT_COLOR)
        rect_diff = title_diff.get_rect(center=(TOTAL_WIDTH // 2, 150))
        self.screen.blit(title_diff, rect_diff)

        self._draw_button(400, 250, 200, 80, 'Easy', self.font)
        self._draw_button(400, 350, 200, 80, 'Medium', self.font)
        self._draw_button(400, 450, 200, 80, 'Hard', self.font)

    def _draw_tutorial_menu(self):
        """Draws the tutorial selection menu."""
        title_tut = self.font.render('Select Puzzle', True, TEXT_COLOR)
        rect_tut = title_tut.get_rect(center=(TOTAL_WIDTH // 2, 150))
        self.screen.blit(title_tut, rect_tut)

        self._draw_button(400, 250, 200, 80, 'Mate in 1', self.font)
        self._draw_button(400, 350, 200, 80, 'Mate in 2', self.font)

    def _draw_paused_overlay(self):
        """Draws a 'PAUSED' overlay."""
        pygame.draw.rect(self.screen, BACKGROUND_COLOR, [0, 0, BOARD_WIDTH, BOARD_HEIGHT], 0, 10) # Semi-transparent overlay
        text_p = self.font.render('PAUSED', True, TEXT_COLOR)
        rect_p = text_p.get_rect(center=(BOARD_WIDTH // 2, BOARD_HEIGHT // 2))
        self.screen.blit(text_p, rect_p)

    def _draw_game_over_popup(self):
        """Draws the game over popup based on game.game_over_status."""
        status = self.game.game_over_status
        text_to_display = ""
        if status == 'white_wins': text_to_display = 'White won by checkmate'
        elif status == 'black_wins': text_to_display = 'Black won by checkmate'
        elif status == 'draw': text_to_display = 'Draw (Stalemate/Material)'
        elif status == 'timeout_w': text_to_display = 'White lost on time'
        elif status == 'timeout_b': text_to_display = 'Black lost on time'
        elif status == 'resigned_w': text_to_display = 'White Resigned - Black Wins'
        elif status == 'resigned_b': text_to_display = 'Black Resigned - White Wins'
        
        text_surface = self.font.render(text_to_display, True, TEXT_COLOR)
        self.draw_popup(text_surface)

# --- Entry point for PyScript ---
# This function will be called when PyScript finishes loading.
async def start_web_game():
    print("PyScript: Initializing Chess Game...")
    game_engine = ChessGame()
    game_ui = WebGameUI(game_engine)
    await game_ui.main_loop()

# Schedule the game to start
asyncio.ensure_future(start_web_game())