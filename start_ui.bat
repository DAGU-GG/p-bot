@echo off
echo PokerStars Bot - Modern UI with Live Recognition
echo ================================================
echo.

cd /d "d:\P-bot 2\project"

echo Checking OBS Virtual Camera connection...
echo Make sure:
echo   1. OBS Studio is running
echo   2. Virtual Camera is started (Tools ^> Virtual Camera ^> Start)
echo   3. PokerStars table is visible in OBS preview
echo.

echo Starting Modern UI with Hardware Capture Integration...
echo.

REM Run the updated launcher with hardware capture
python run_ui.py

REM If that fails, try direct hardware capture test
if %errorlevel% neq 0 (
    echo.
    echo UI failed, testing hardware capture directly...
    python hardware_capture_integration.py
)

REM If still fails, try basic UI without hardware capture
if %errorlevel% neq 0 (
    echo.
    echo Trying basic UI without hardware capture...
    set PYTHONPATH=d:\P-bot 2\project;d:\P-bot 2\project\src
    python src/ui/main_window.py
)

echo.
echo Press any key to exit...
pause > nul
