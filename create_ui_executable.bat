@echo off
echo ========================================
echo PokerStars Bot - Create GUI Executable
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
echo Installing PyInstaller...
pip install pyinstaller

echo.
echo Creating GUI executable...
echo This may take several minutes...

pyinstaller --onefile --windowed --name "PokerStarsBotGUI" ^
    --add-data "src;src" ^
    --add-data "requirements.txt;." ^
    --icon=poker_icon.ico ^
    --hidden-import=cv2 ^
    --hidden-import=numpy ^
    --hidden-import=pyautogui ^
    --hidden-import=pygetwindow ^
    --hidden-import=mss ^
    --hidden-import=keyboard ^
    --hidden-import=mouse ^
    --hidden-import=pytesseract ^
    --hidden-import=PIL ^
    --hidden-import=tkinter ^
    --hidden-import=threading ^
    src/bot_ui.py

if %errorlevel% neq 0 (
    echo ERROR: Failed to create executable
    pause
    exit /b 1
)

echo.
echo ========================================
echo GUI Executable created successfully!
echo ========================================
echo.
echo Location: dist\PokerStarsBotGUI.exe
echo.
echo FEATURES:
echo - Complete graphical user interface
echo - Real-time monitoring and testing
echo - Interactive card recognition
echo - Debug tools and configuration
echo - No command line required
echo.
echo IMPORTANT: 
echo - The .exe file needs Tesseract OCR installed
echo - Copy the entire project folder when distributing
echo - Test the executable before distributing
echo.
pause