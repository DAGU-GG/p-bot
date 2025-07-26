@echo off
echo Testing Four-Color Suit Detection System
echo ======================================

echo Ensuring required directories exist...
if not exist debug_cards mkdir debug_cards
if not exist debug_cards\improved mkdir debug_cards\improved
if not exist debug_color_detection mkdir debug_color_detection

echo Running four-color suit tests...
python test_four_color_suits.py

echo Test complete! Check test_four_color_suits.log for detailed results.
pause
