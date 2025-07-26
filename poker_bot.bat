@echo off
echo ========================================
echo PokerStars Bot - Main Application
echo ========================================
echo.

if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found
    echo Please run setup.bat first
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Starting PokerStars Bot...
echo.
echo IMPORTANT: 
echo 1. Make sure PokerStars is running
echo 2. Open a poker table (play money recommended for testing)
echo 3. Press Ctrl+C to stop the bot
echo.
echo Bot is starting in 3 seconds...
timeout /t 3 /nobreak > nul

python src/poker_bot.py

echo.
echo Bot stopped.
pause