@echo off
echo Installing dependencies for direct card recognition...

pip install opencv-python numpy pytesseract

echo.
echo NOTE: You also need to install Tesseract OCR on your system:
echo 1. Download Tesseract OCR from: https://github.com/UB-Mannheim/tesseract/wiki
echo 2. Install it with default options
echo 3. Ensure the path is added to your system environment variables

echo.
echo Dependencies installed successfully!
pause
