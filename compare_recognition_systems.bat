@echo off
echo Comparing card recognition systems...
echo This will test all three recognition systems on the same test images

python compare_recognition_systems.py

if %ERRORLEVEL% EQU 0 (
    echo Comparison completed successfully!
    echo See recognition_comparison_results.md for detailed results
    echo Opening results...
    start recognition_comparison_results.md
) else (
    echo Comparison failed. Please check recognition_comparison.log for details.
)
pause
