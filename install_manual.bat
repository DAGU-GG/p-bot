@echo off
echo ========================================
echo PokerStars Bot - Manual Installation
echo ========================================
echo.
echo This script will install packages one by one for better compatibility
echo.

if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing packages individually...

echo Installing OpenCV...
pip install opencv-python
if %errorlevel% neq 0 (
    echo WARNING: OpenCV installation failed, trying alternative...
    pip install opencv-python-headless
)

echo Installing PyAutoGUI...
pip install pyautogui

echo Installing Pillow...
pip install pillow

echo Installing NumPy...
pip install numpy

echo Installing PyGetWindow...
pip install pygetwindow

echo Installing MSS...
pip install mss

echo Installing Keyboard...
pip install keyboard

echo Installing Mouse...
pip install mouse

echo Installing PyTesseract...
pip install pytesseract

echo.
echo Testing imports...
python -c "import cv2; print('✓ OpenCV imported successfully')"
python -c "import pyautogui; print('✓ PyAutoGUI imported successfully')"
python -c "import PIL; print('✓ Pillow imported successfully')"
python -c "import numpy; print('✓ NumPy imported successfully')"
python -c "import pygetwindow; print('✓ PyGetWindow imported successfully')"
python -c "import mss; print('✓ MSS imported successfully')"
python -c "import keyboard; print('✓ Keyboard imported successfully')"
python -c "import mouse; print('✓ Mouse imported successfully')"

echo.
echo Creating directories...
if not exist "screenshots" mkdir screenshots
if not exist "debug_images" mkdir debug_images
if not exist "debug_cards" mkdir debug_cards
if not exist "debug_community" mkdir debug_community
if not exist "card_templates" mkdir card_templates
if not exist "regions" mkdir regions

echo.
echo ========================================
echo Manual installation completed!
echo ========================================
echo.
echo Next steps:
echo 1. Install Tesseract OCR (see INSTALL_GUIDE.md)
echo 2. Run test_environment.bat to verify everything works
echo 3. Run poker_bot.bat to start the bot
echo.
pause