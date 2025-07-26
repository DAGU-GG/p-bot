@echo off
echo ========================================
echo PokerStars Bot - Modern UI Application
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
echo Verifying card recognition modules...
if not exist "improved_card_recognition.py" (
    echo ERROR: Required module improved_card_recognition.py not found
    pause
    exit /b 1
)

if not exist "direct_card_recognition.py" (
    echo WARNING: Direct card recognition module not found
    echo The application will use improved recognition only
    timeout /t 3 >nul
)

echo Checking region configuration...
if not exist "region_config.json" (
    echo ERROR: region_config.json not found in the current directory
    echo Please ensure the configuration file exists
    pause
    exit /b 1
)

echo.
echo Starting Modern PokerStars Bot UI...
echo.
echo FEATURES:
echo - Beautiful, professional interface
echo - Real-time poker table visualization
echo - Enhanced player detection (9-max support)
echo - Live card recognition display with improved accuracy
echo - Direct and improved card recognition systems
echo - Color analysis and empty slot detection
echo - Visible region overlays on the livestream
echo - Modern graphics and intuitive controls
echo - Comprehensive game state monitoring
echo.
echo Starting application with advanced card recognition...

REM Path to region configuration
SET REGION_CONFIG=D:\P-bot 2\project\regions\region_config.json

REM Check if region config exists in the specified path
if not exist "%REGION_CONFIG%" (
    echo WARNING: Region configuration not found at %REGION_CONFIG%
    echo Falling back to default configuration
    SET REGION_CONFIG=region_config.json
)

REM Start the application with improved card recognition and region visualization
python src/modern_ui.py --recognition=improved --show-regions --config="%REGION_CONFIG%"

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Application failed to start
    echo Check the error messages above
    pause
    exit /b 1
)

echo.
echo Application closed.
pause