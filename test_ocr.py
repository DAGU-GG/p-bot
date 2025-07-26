"""
Test OCR functionality with pytesseract and Tesseract
"""
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_pytesseract():
    """Test if pytesseract can import and find Tesseract"""
    try:
        import pytesseract
        print("✅ pytesseract imported successfully")
        
        # Try to get Tesseract version
        try:
            version = pytesseract.get_tesseract_version()
            print(f"✅ Tesseract version: {version}")
            return True
        except Exception as e:
            print(f"❌ Could not get Tesseract version: {e}")
            
            # Try to set the path manually
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            try:
                version = pytesseract.get_tesseract_version()
                print(f"✅ Tesseract version (after setting path): {version}")
                return True
            except Exception as e2:
                print(f"❌ Still could not find Tesseract: {e2}")
                return False
                
    except ImportError as e:
        print(f"❌ Could not import pytesseract: {e}")
        return False

def test_bot_components():
    """Test if bot components can initialize with OCR"""
    try:
        from card_recognizer import CardRecognizer
        recognizer = CardRecognizer()
        
        # Check if OCR warning appears
        print("✅ CardRecognizer initialized")
        
        stats = recognizer.get_recognition_stats()
        print(f"Templates loaded: {stats['templates_loaded']}")
        print(f"OCR available: {stats.get('ocr_available', 'Unknown')}")
        
        return True
    except Exception as e:
        print(f"❌ Error initializing CardRecognizer: {e}")
        return False

def main():
    print("=== OCR Functionality Test ===")
    
    ocr_works = test_pytesseract()
    bot_works = test_bot_components()
    
    print(f"\n=== Results ===")
    print(f"OCR Available: {'✅ Yes' if ocr_works else '❌ No'}")
    print(f"Bot Components: {'✅ Working' if bot_works else '❌ Failed'}")
    
    if ocr_works and bot_works:
        print("\n🎉 OCR is fully functional! The bot can now use both template matching AND OCR for card recognition.")
    elif bot_works:
        print("\n⚠️ Bot works but OCR might have issues. Template matching should still work.")
    else:
        print("\n❌ There are issues that need to be resolved.")

if __name__ == "__main__":
    main()
