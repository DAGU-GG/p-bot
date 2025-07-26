@echo off
echo Starting poker bot with improved card recognition...
python update_card_recognition.py
if %ERRORLEVEL% EQU 0 (
    echo Improved card recognition system integrated successfully!
    echo Running poker bot...
    poker_bot.bat
) else (
    echo Failed to integrate improved card recognition system.
    echo Please check the logs for details.
    pause
)
