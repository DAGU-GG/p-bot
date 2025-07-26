@echo off
echo Starting poker bot with direct card recognition...
echo Logging to direct_poker_bot.log

python poker_bot.py --recognition=direct --log=direct_poker_bot.log

if %ERRORLEVEL% EQU 0 (
    echo Poker bot completed successfully!
) else (
    echo Poker bot encountered an error. Please check direct_poker_bot.log for details.
)
pause
