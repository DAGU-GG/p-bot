@echo off
echo ========================================
echo PokerStars Bot - Card Recognition Test
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
echo Starting Card Recognition Tests...
echo.

REM Create necessary directories if they don't exist
if not exist "debug_cards" mkdir debug_cards
if not exist "debug_images" mkdir debug_images
if not exist "test_output" mkdir test_output
if not exist "recognition_results" mkdir recognition_results

echo Test options:
echo 1. Live Screen Capture Test
echo 2. Card Color Detection Test
echo 3. Simple Card Recognition Test
echo 4. Exit

choice /C 1234 /N /M "Select test to run (1-4): "

if %errorlevel% == 1 (
    echo.
    echo Running Live Screen Capture Test...
    echo This will:
    echo - Capture your current screen
    echo - Process it for card detection
    echo - Save debug images in debug_cards and debug_images folders
    echo.
    python test_card_recognition.py --live
)

if %errorlevel% == 2 (
    echo.
    echo Testing Card Color Detection...
    python test_card_color.py
)

if %errorlevel% == 3 (
    echo.
    echo Testing Simple Card Recognition...
    python simple_card_recognition_test.py --directory debug_cards
)

if %errorlevel% == 4 (
    echo Exiting...
    exit /b 0
)

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Test failed to run
    echo Check the error messages above
    pause
    exit /b 1
)

echo.
echo Test complete. Check the debug_cards, debug_images, and test_output folders for results.
pause
