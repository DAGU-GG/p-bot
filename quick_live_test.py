"""
Quick Live PokerStars Test - Immediate Capture and Analysis
"""
import cv2
import numpy as np
import pyautogui
import time
from pathlib import Path
from tesseract_config import configure_tesseract
import pytesseract

# Configure Tesseract
configure_tesseract()

def capture_obs_window():
    """Capture screenshot of OBS window showing PokerStars"""
    try:
        # Take screenshot
        screenshot = pyautogui.screenshot()
        screenshot_np = np.array(screenshot)
        screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
        
        # Save for verification
        timestamp = int(time.time())
        filename = f"live_pokerstars_capture_{timestamp}.png"
        cv2.imwrite(filename, screenshot_bgr)
        print(f"Screenshot saved as: {filename}")
        
        return screenshot_bgr, filename
    except Exception as e:
        print(f"Error capturing screenshot: {e}")
        return None, None

def quick_ocr_analysis(image):
    """Quick OCR analysis of the captured image"""
    try:
        # Convert to grayscale for better OCR
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply simple preprocessing
        _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        
        # Run OCR
        text = pytesseract.image_to_string(thresh, config='--psm 6')
        
        print("\n=== OCR TEXT FOUND ===")
        print(text)
        print("=====================")
        
        # Look for poker-related terms
        poker_terms = ['fold', 'call', 'raise', 'check', 'bet', 'all-in', '$', 'chips', 'pot']
        found_terms = [term for term in poker_terms if term.lower() in text.lower()]
        
        if found_terms:
            print(f"\nPoker terms detected: {found_terms}")
            return True
        else:
            print("\nNo poker terms detected in OCR")
            return False
            
    except Exception as e:
        print(f"Error in OCR analysis: {e}")
        return False

def main():
    print("Quick Live PokerStars Test")
    print("=========================")
    print("This will capture your current screen and analyze it for poker content")
    print()
    
    # Capture
    image, filename = capture_obs_window()
    
    if image is not None:
        print(f"Image captured successfully: {image.shape}")
        
        # Analyze
        poker_detected = quick_ocr_analysis(image)
        
        if poker_detected:
            print("\n✅ SUCCESS: Poker table detected!")
            print("Your hardware setup is working correctly.")
        else:
            print("\n⚠️  No poker content detected")
            print("Make sure PokerStars is visible on your laptop screen")
            print("and OBS is capturing the laptop display")
            
    else:
        print("❌ Failed to capture image")
    
    print(f"\nCapture saved as: {filename}")
    print("Test completed!")

if __name__ == "__main__":
    main()
