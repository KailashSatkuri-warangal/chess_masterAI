@echo off
REM Simple run script for Chess Game (Windows)
REM If a venv doesn't exist, this will create one and install dependencies.

if not exist venv (
  echo Creating virtual environment...
  python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing dependencies from requirements.txt...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
  echo Failed to install from requirements.txt, trying to install pygame directly...
  python -m pip install pygame
)

echo Starting game...
python playchess.py

echo Game exited. Press any key to close.
pause
