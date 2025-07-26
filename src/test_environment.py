"""
Environment Test Script
This script tests that all required libraries are properly installed
and can be imported successfully.
"""

import sys
import importlib

def test_import(module_name, description=""):
    """Test if a module can be imported successfully."""
    try:
        importlib.import_module(module_name)
        print(f"✓ {module_name} - {description}")
        return True
    except ImportError as e:
        print(f"✗ {module_name} - {description} - ERROR: {e}")
        return False

def test_opencv():
    """Test OpenCV functionality."""
    try:
        import cv2
        print(f"✓ OpenCV version: {cv2.__version__}")
        
        # Test basic functionality
        import numpy as np
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        gray = cv2.cvtColor(test_image, cv2.COLOR_BGR2GRAY)
        
        # Test edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Test contour detection
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        print("✓ OpenCV basic functionality working")
        print("✓ OpenCV edge detection working")
        print("✓ OpenCV contour detection working")
        return True
    except Exception as e:
        print(f"✗ OpenCV test failed: {e}")
        return False

def test_pyautogui():
    """Test PyAutoGUI functionality."""
    try:
        import pyautogui
        
        # Get screen size
        screen_width, screen_height = pyautogui.size()
        print(f"✓ PyAutoGUI - Screen size: {screen_width}x{screen_height}")
        
        # Test screenshot capability
        screenshot = pyautogui.screenshot()
        print(f"✓ PyAutoGUI - Screenshot captured: {screenshot.size}")
        return True
    except Exception as e:
        print(f"✗ PyAutoGUI test failed: {e}")
        return False

def test_window_detection():
    """Test window detection functionality."""
    try:
        import pygetwindow as gw
        
        windows = gw.getAllWindows()
        print(f"✓ Window detection - Found {len(windows)} windows")
        
        # List some window titles for debugging
        print("Sample window titles:")
        for i, window in enumerate(windows[:5]):
            if window.title:
                print(f"  - {window.title}")
        
        return True
    except Exception as e:
        print(f"✗ Window detection test failed: {e}")
        return False

def test_image_processing():
    """Test image processing functionality."""
    try:
        from image_processor import ImageProcessor, GameState
        from card_recognizer import CardRecognizer
        from community_card_detector import CommunityCardDetector
        from community_card_detector import CommunityCardDetector
        
        # Create test processor
        processor = ImageProcessor()
        print("✓ Image processor created successfully")
        
        # Create test card recognizer
        recognizer = CardRecognizer()
        print("✓ Card recognizer created successfully")
        
        # Create test community card detector
        community_detector = CommunityCardDetector(recognizer)
        print("✓ Community card detector created successfully")
        
        # Create test community card detector
        community_detector = CommunityCardDetector(recognizer)
        print("✓ Community card detector created successfully")
        
        # Create test image
        import numpy as np
        test_image = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)
        
        # Test preprocessing
        processed = processor.preprocess_image(test_image, "test")
        print(f"✓ Image preprocessing working - {len(processed)} variants created")
        
        # Test region calibration
        success = processor.calibrate_table_regions(test_image)
        print(f"✓ Table calibration: {'successful' if success else 'failed (expected with random image)'}")
        
        # Test game state analysis
        game_state = processor.analyze_table_state(test_image)
        print(f"✓ Game state analysis working - detected {game_state.active_players} active players")
        
        # Test card recognition stats
        stats = recognizer.get_recognition_stats()
        print(f"✓ Card recognition initialized - {stats['templates_loaded']} templates loaded")
        
        # Test community card detection stats
        community_stats = community_detector.get_detection_stats()
        print(f"✓ Community card detection initialized - {community_stats['regions_defined']} regions defined")
        
        # Test community card detection stats
        community_stats = community_detector.get_detection_stats()
        print(f"✓ Community detection initialized - {community_stats['regions_defined']} regions defined")
        
        return True
    except Exception as e:
        print(f"✗ Image processing test failed: {e}")
        return False

def main():
    """Run all environment tests."""
    print("PokerStars Bot - Environment Test")
    print("=" * 40)
    print(f"Python version: {sys.version}")
    print("=" * 40)
    
    tests = [
        ("cv2", "OpenCV for image processing"),
        ("pyautogui", "PyAutoGUI for automation"),
        ("PIL", "Pillow for image handling"),
        ("numpy", "NumPy for array operations"),
        ("pygetwindow", "Window detection"),
        ("mss", "Fast screen capture"),
        ("keyboard", "Keyboard input detection"),
        ("mouse", "Mouse input detection"),
    ]
    
    print("Testing library imports:")
    print("-" * 30)
    
    all_passed = True
    for module, description in tests:
        if not test_import(module, description):
            all_passed = False
    
    print("\nTesting functionality:")
    print("-" * 30)
    
    if not test_opencv():
        all_passed = False
    
    if not test_pyautogui():
        all_passed = False
    
    if not test_window_detection():
        all_passed = False
    
    if not test_image_processing():
        all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("✓ All tests passed! Environment is ready.")
        print("\nNext steps:")
        print("1. Start PokerStars")
        print("2. Open a poker table")
        print("3. Run: python src/poker_bot.py")
        print("\nStage 2 Features:")
        print("- Automatic table region calibration")
        print("- Card detection in player and community areas")
        print("- Dealer button detection")
        print("- Basic text recognition for pot amounts")
        print("- Comprehensive game state analysis")
        print("\nStage 3 Features:")
        print("- Hero hole card recognition with template matching")
        print("- OCR fallback for robust card identification")
        print("- Confidence scoring and validation")
        print("- Debug image saving for analysis")
        print("\nStage 4 Features:")
        print("- Community card detection (flop, turn, river)")
        print("- Progressive revelation support")
        print("- Multi-method card presence detection")
        print("- Phase-aware game state tracking")
        print("\nStage 3 Features:")
        print("- Hero hole card recognition with template matching")
        print("- OCR fallback for robust card identification")
        print("- Confidence scoring and validation")
        print("- Debug image saving for analysis")
        print("\nStage 4 Features:")
        print("- Community card detection (flop, turn, river)")
        print("- Progressive revelation handling")
        print("- Card presence detection with multiple methods")
        print("- Phase identification and validation")
    else:
        print("✗ Some tests failed. Please install missing dependencies:")
        print("pip install -r requirements.txt")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())