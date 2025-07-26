@echo off
echo ========================================
echo PokerStars Bot - Setup Script
echo ========================================
echo.

echo Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo.
echo Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing required packages...
pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install packages
    echo Trying alternative installation method...
    pip install opencv-python pyautogui pillow numpy pygetwindow mss keyboard mouse pytesseract
    if %errorlevel% neq 0 (
        echo ERROR: Package installation failed
        echo Please check your internet connection and Python version compatibility
        pause
        exit /b 1
    )
    echo Alternative installation successful!
)

echo.
echo Verifying installation...
python -c "import cv2, pyautogui, PIL, numpy; print('All packages imported successfully!')"
if %errorlevel% neq 0 (
    echo WARNING: Some packages may not be properly installed
    echo Please run test_environment.bat to verify
)

echo.
echo Creating necessary directories...
if not exist "screenshots" mkdir screenshots
if not exist "debug_images" mkdir debug_images
if not exist "debug_cards" mkdir debug_cards
if not exist "debug_community" mkdir debug_community
if not exist "card_templates" mkdir card_templates
if not exist "regions" mkdir regions
    pause
    exit /b 1
)

echo.
echo ========================================
echo Setup completed successfully!
echo ========================================
echo.
echo Next steps:
echo 1. Install Tesseract OCR (see README.md for instructions)
echo 2. Run test_environment.bat to verify setup
echo 3. Run poker_bot.bat to start the bot
echo.
pause