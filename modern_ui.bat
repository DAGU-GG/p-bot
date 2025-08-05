@echo off
echo PokerStars Bot - Modern UI with Live Recognition
echo ================================================
echo.
echo This will launch the bot with:
echo   • Ultimate Card Recognition System
echo   • Hardware Capture Integration (OBS Virtual Camera)
echo   • Real-time poker table analysis
echo   • Live UI with recognition feedback
echo.

cd /d "d:\P-bot 2\project"

echo Starting Enhanced PokerBot...
python run_ui.py

if %errorlevel% neq 0 (
    echo.
    echo Launch failed. Check that:
    echo   1. OBS Studio is running with Virtual Camera started
    echo   2. All Python dependencies are installed
    echo   3. PokerStars table is visible in OBS
    echo.
    pause
)