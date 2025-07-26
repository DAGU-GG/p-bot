@echo off
cls
echo ==========================================================
echo               P-Bot Card Recognition System
echo ==========================================================
echo.
echo  1. Run Direct Card Recognition Tests
echo  2. Update Poker Bot to use Direct Recognition
echo  3. Run Poker Bot with Direct Recognition
echo  4. Compare All Recognition Systems
echo  5. View Documentation
echo  0. Exit
echo.
echo ==========================================================
echo.

set /p choice=Enter your choice (0-5): 

if "%choice%"=="1" (
    call test_direct_recognition.bat
    goto menu
)
if "%choice%"=="2" (
    call update_direct_recognition.bat
    goto menu
)
if "%choice%"=="3" (
    call run_direct_poker_bot.bat
    goto menu
)
if "%choice%"=="4" (
    call compare_recognition_systems.bat
    goto menu
)
if "%choice%"=="5" (
    start notepad DIRECT_RECOGNITION.md
    goto menu
)
if "%choice%"=="0" (
    exit /b
)

echo Invalid choice!
pause
goto menu

:menu
cls
goto :EOF
