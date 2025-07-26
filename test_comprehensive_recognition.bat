@echo off
REM Run the comprehensive card recognition test

echo Running comprehensive card recognition test...

REM Set up Python environment
call setup.bat

REM Test on different card images
python comprehensive_card_recognition.py --image "debug_cards\extracted_hero_card1_1753524641475.png" --debug
python comprehensive_card_recognition.py --image "debug_cards\extracted_card_1_1753524963742.png" --debug

echo Tests completed. Check the log file for results.
