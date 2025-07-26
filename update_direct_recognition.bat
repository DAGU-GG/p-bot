@echo off
echo Updating poker bot to use direct card recognition system...
python update_direct_recognition.py
if %ERRORLEVEL% EQU 0 (
    echo Direct card recognition system integrated successfully!
    echo Run the poker bot with run_direct_poker_bot.bat
) else (
    echo Failed to update poker bot. Please check the logs.
)
pause
