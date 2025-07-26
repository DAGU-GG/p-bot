@echo off
echo ========================================
echo PokerStars Bot - Window Finder Tool
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
echo Starting window finder tool...
echo This tool helps you find and test PokerStars windows
echo.
python src/window_finder.py

pause