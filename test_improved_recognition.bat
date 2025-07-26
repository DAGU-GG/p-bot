@echo off
echo Testing improved card recognition system...
python test_improved_recognition.py
if %ERRORLEVEL% EQU 0 (
    echo All tests passed successfully!
) else (
    echo Some tests failed! Check the log for details.
)
pause
