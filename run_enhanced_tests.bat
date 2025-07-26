@echo off
echo Enhanced Card Recognition Test Suite
echo =====================================

echo.
echo Testing standard recognition...
python test_enhanced_recognition.py --method standard --dir debug_images

echo.
echo Testing enhanced recognition...
python test_enhanced_recognition.py --method enhanced --dir debug_images

echo.
echo Testing color detection...
python test_enhanced_recognition.py --method color --dir debug_images

echo.
echo Comparing all methods...
python test_enhanced_recognition.py --method compare --dir debug_images --debug

echo.
echo Testing complete! Check the debug_comparison directory for visual results.
pause
