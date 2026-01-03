# d:/8thsem/chess_masterAI/web_main.py

# This is the main entry point for PyScript.
# It initializes the game UI and starts the main loop.

import asyncio
import js # Import js to ensure it's available for early prints if needed
print("PyScript: web_main.py started execution.") # Very early print
from web_ui.web_game_ui import start_web_game

# PyScript will automatically run the asyncio task scheduled by start_web_game()
asyncio.ensure_future(start_web_game())
print("PyScript: start_web_game scheduled.")