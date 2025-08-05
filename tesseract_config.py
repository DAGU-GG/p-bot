"""
Tesseract OCR Configuration Utility
Centralizes Tesseract path configuration for the entire project
"""

import os
import sys

def configure_tesseract():
    """Configure Tesseract OCR path for the project"""
    try:
        import pytesseract
        
        # Set Tesseract path to local installation
        tesseract_path = r'D:\P-bot 2\project\Tesseract\tesseract.exe'
        
        # Verify the executable exists
        if os.path.exists(tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            print(f"✅ Tesseract configured: {tesseract_path}")
            return True
        else:
            print(f"❌ Tesseract not found at: {tesseract_path}")
            
            # Try alternative paths
            alternative_paths = [
                r'D:\P-bot 2\project\Tesseract\bin\tesseract.exe',
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'
            ]
            
            for alt_path in alternative_paths:
                if os.path.exists(alt_path):
                    pytesseract.pytesseract.tesseract_cmd = alt_path
                    print(f"✅ Tesseract found at alternative location: {alt_path}")
                    return True
            
            print("❌ Tesseract executable not found in any expected location")
            return False
            
    except ImportError:
        print("❌ pytesseract module not installed")
        return False

def test_tesseract():
    """Test if Tesseract is working correctly"""
    try:
        import pytesseract
        import numpy as np
        from PIL import Image
        
        # Create a simple test image with text
        test_img = Image.new('RGB', (200, 50), color='white')
        
        # Try to run OCR on the test image
        text = pytesseract.image_to_string(test_img)
        print("✅ Tesseract OCR test successful")
        return True
        
    except Exception as e:
        print(f"❌ Tesseract OCR test failed: {e}")
        return False

def get_tesseract_version():
    """Get Tesseract version information"""
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        print(f"📋 Tesseract version: {version}")
        return version
    except Exception as e:
        print(f"❌ Could not get Tesseract version: {e}")
        return None

if __name__ == "__main__":
    print("🔧 Tesseract Configuration Check")
    print("=" * 40)
    
    if configure_tesseract():
        get_tesseract_version()
        test_tesseract()
    else:
        print("❌ Tesseract configuration failed")
        sys.exit(1)
