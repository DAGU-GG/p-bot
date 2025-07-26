@echo off
echo ========================================
echo PokerStars Bot - Cleanup Script
echo ========================================
echo.

echo Cleaning up temporary files and folders...

if exist "venv" (
    echo Removing virtual environment...
    rmdir /s /q venv
)

if exist "build" (
    echo Removing build folder...
    rmdir /s /q build
)

if exist "dist" (
    echo Removing dist folder...
    rmdir /s /q dist
)

if exist "*.spec" (
    echo Removing spec files...
    del /q *.spec
)

if exist "__pycache__" (
    echo Removing Python cache...
    rmdir /s /q __pycache__
)

if exist "src\__pycache__" (
    echo Removing src cache...
    rmdir /s /q src\__pycache__
)

if exist "*.log" (
    echo Removing log files...
    del /q *.log
)

echo.
echo Cleanup completed!
echo Run setup.bat to reinstall the environment.
pause