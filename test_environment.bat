@echo off
echo ========================================
echo PokerStars Bot - Environment Test
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
echo Running environment tests...
python src/test_environment.py

echo.
echo Test completed. Check output above for any errors.
pause