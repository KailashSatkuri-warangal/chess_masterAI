# d:/8thsem/chess_masterAI/web_main.py

# This is the main entry point for PyScript.
# It initializes the game UI and starts the main loop.

import asyncio
from web_ui.web_game_ui import start_web_game

# PyScript will automatically run the asyncio task scheduled by start_web_game()
asyncio.ensure_future(start_web_game())