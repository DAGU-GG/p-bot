"""
Window Finder Utility
This utility helps identify and test window detection for PokerStars.
"""

import pygetwindow as gw
import time
import cv2
import numpy as np
from mss import mss

def list_all_windows():
    """List all currently open windows."""
    print("All open windows:")
    print("-" * 50)
    
    windows = gw.getAllWindows()
    
    for i, window in enumerate(windows):
        if window.title.strip():  # Only show windows with titles
            print(f"{i+1:3d}. Title: '{window.title}'")
            print(f"     Position: ({window.left}, {window.top})")
            print(f"     Size: {window.width}x{window.height}")
            print(f"     Visible: {window.visible}")
            print()

def find_pokerstars_windows():
    """Find potential PokerStars windows."""
    print("Searching for PokerStars windows:")
    print("-" * 50)
    
    search_terms = [
        "pokerstars", "poker", "hold'em", "omaha", "tournament", 
        "cash", "table", "nlhe", "plo"
    ]
    
    windows = gw.getAllWindows()
    found_windows = []
    
    for window in windows:
        if window.title.strip():
            title_lower = window.title.lower()
            for term in search_terms:
                if term in title_lower:
                    found_windows.append(window)
                    print(f"Found: '{window.title}'")
                    print(f"  Position: ({window.left}, {window.top})")
                    print(f"  Size: {window.width}x{window.height}")
                    print()
                    break
    
    if not found_windows:
        print("No PokerStars windows found.")
        print("Make sure PokerStars is running and a table is open.")
    
    return found_windows

def test_screen_capture(window):
    """Test screen capture for a specific window."""
    print(f"Testing screen capture for: '{window.title}'")
    print("-" * 50)
    
    try:
        # Set up capture region
        capture_region = {
            'top': window.top,
            'left': window.left,
            'width': window.width,
            'height': window.height
        }
        
        print(f"Capture region: {capture_region}")
        
        # Capture screen
        with mss() as sct:
            screenshot = sct.grab(capture_region)
            
            # Convert to numpy array
            img_array = np.array(screenshot)
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_BGRA2BGR)
            
            # Save test image
            filename = f"test_capture_{int(time.time())}.png"
            cv2.imwrite(filename, img_bgr)
            
            print(f"✓ Screen capture successful!")
            print(f"✓ Image saved as: {filename}")
            print(f"✓ Image size: {img_bgr.shape}")
            
            return True
            
    except Exception as e:
        print(f"✗ Screen capture failed: {e}")
        return False

def interactive_window_selector():
    """Interactive window selection for testing."""
    pokerstars_windows = find_pokerstars_windows()
    
    if not pokerstars_windows:
        print("\nNo PokerStars windows found automatically.")
        print("Showing all windows instead...")
        list_all_windows()
        return
    
    if len(pokerstars_windows) == 1:
        window = pokerstars_windows[0]
        print(f"Found one PokerStars window: '{window.title}'")
        
        response = input("Test screen capture for this window? (y/n): ")
        if response.lower() == 'y':
            test_screen_capture(window)
    else:
        print(f"Found {len(pokerstars_windows)} PokerStars windows:")
        for i, window in enumerate(pokerstars_windows):
            print(f"{i+1}. {window.title}")
        
        try:
            choice = int(input("Select window number to test: ")) - 1
            if 0 <= choice < len(pokerstars_windows):
                test_screen_capture(pokerstars_windows[choice])
            else:
                print("Invalid selection.")
        except ValueError:
            print("Invalid input.")

def main():
    """Main function for window finder utility."""
    print("PokerStars Window Finder & Capture Tester")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. List all windows")
        print("2. Find PokerStars windows")
        print("3. Interactive window selector")
        print("4. Exit")
        
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == '1':
            list_all_windows()
        elif choice == '2':
            find_pokerstars_windows()
        elif choice == '3':
            interactive_window_selector()
        elif choice == '4':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please select 1-4.")

if __name__ == "__main__":
    main()