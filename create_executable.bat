@echo off
echo ========================================
echo PokerStars Bot - Create Executable
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
echo Creating executable...
echo This may take several minutes...

pyinstaller --onefile --windowed --name "PokerStarsBot" ^
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
    src/poker_bot.py

if %errorlevel% neq 0 (
    echo ERROR: Failed to create executable
    pause
    exit /b 1
)

echo.
echo ========================================
echo Executable created successfully!
echo ========================================
echo.
echo Location: dist\PokerStarsBot.exe
echo.
echo IMPORTANT: 
echo - The .exe file needs Tesseract OCR installed on the target system
echo - Copy the entire project folder structure when distributing
echo - Test the executable before distributing
echo.
pause