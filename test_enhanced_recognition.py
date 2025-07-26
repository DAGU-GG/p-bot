"""
Enhanced Card Recognition Test

This script tests the enhanced card recognition system which combines
template matching with color-based suit detection.

Usage:
    python test_enhanced_recognition.py [--debug] [--dir DIR] [--method METHOD]
    
Options:
    --debug     Enable debug mode to save debug images
    --dir DIR   Directory with card images to test (default: debug_images)
    --method    Recognition method: 'standard', 'enhanced', 'color', or 'compare' (default: 'compare')
"""

import os
import sys
import cv2
import numpy as np
import argparse
import logging
import time
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import recognizers - try different import strategies
try:
    from src.card_recognizer import CardRecognizer
    from src.enhanced_card_recognizer import EnhancedCardRecognizer
    from src.card_suit_color_detector import CardSuitColorDetector
except ImportError:
    try:
        sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))
        from card_recognizer import CardRecognizer
        from enhanced_card_recognizer import EnhancedCardRecognizer
        from card_suit_color_detector import CardSuitColorDetector
    except ImportError as e:
        print(f"Error importing modules: {e}")
        print("Make sure the src directory contains all required modules.")
        sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('test_enhanced_recognition')

def test_standard_recognition(image_path, debug=False):
    """
    Test standard card recognition.
    
    Args:
        image_path: Path to card image
        debug: Whether to save debug images
        
    Returns:
        Recognized card or None
    """
    recognizer = CardRecognizer()
    img = cv2.imread(image_path)
    
    if img is None:
        logger.error(f"Could not read image: {image_path}")
        return None
    
    start_time = time.time()
    card = recognizer.recognize_card(img, debug)
    end_time = time.time()
    
    if card:
        logger.info(f"Standard recognition: {card} (confidence: {card.confidence:.2f}, time: {(end_time-start_time)*1000:.0f}ms)")
    else:
        logger.info(f"Standard recognition failed (time: {(end_time-start_time)*1000:.0f}ms)")
    
    return card

def test_enhanced_recognition(image_path, debug=False):
    """
    Test enhanced card recognition.
    
    Args:
        image_path: Path to card image
        debug: Whether to save debug images
        
    Returns:
        Recognized card or None
    """
    recognizer = EnhancedCardRecognizer()
    img = cv2.imread(image_path)
    
    if img is None:
        logger.error(f"Could not read image: {image_path}")
        return None
    
    start_time = time.time()
    card = recognizer.recognize_card(img, debug)
    end_time = time.time()
    
    if card:
        logger.info(f"Enhanced recognition: {card} (confidence: {card.confidence:.2f}, time: {(end_time-start_time)*1000:.0f}ms)")
    else:
        logger.info(f"Enhanced recognition failed (time: {(end_time-start_time)*1000:.0f}ms)")
    
    return card

def test_color_recognition(image_path, debug=False):
    """
    Test color-based suit detection.
    
    Args:
        image_path: Path to card image
        debug: Whether to save debug images
        
    Returns:
        Tuple of (color, confidence)
    """
    detector = CardSuitColorDetector()
    img = cv2.imread(image_path)
    
    if img is None:
        logger.error(f"Could not read image: {image_path}")
        return None, 0
    
    start_time = time.time()
    color, confidence = detector.detect_suit_color(img, debug)
    end_time = time.time()
    
    logger.info(f"Color detection: {color} (confidence: {confidence:.2f}, time: {(end_time-start_time)*1000:.0f}ms)")
    
    return color, confidence

def compare_methods(image_path, debug=False):
    """
    Compare all recognition methods on a single image.
    
    Args:
        image_path: Path to card image
        debug: Whether to save debug images
        
    Returns:
        Dict with results from all methods
    """
    img = cv2.imread(image_path)
    if img is None:
        logger.error(f"Could not read image: {image_path}")
        return None
    
    # Get image filename for output
    image_name = os.path.basename(image_path)
    logger.info(f"Analyzing image: {image_name}")
    
    # Create comparison display
    display = img.copy()
    h, w = display.shape[:2]
    display = cv2.resize(display, (w*2, h*2))
    
    # Test all methods
    results = {}
    
    # Standard recognition
    start_time = time.time()
    std_recognizer = CardRecognizer()
    std_card = std_recognizer.recognize_card(img, debug)
    std_time = (time.time() - start_time) * 1000
    
    if std_card:
        std_text = f"{std_card.rank}{std_card.suit} ({std_card.confidence:.2f})"
    else:
        std_text = "Failed"
    
    results['standard'] = {
        'card': std_card,
        'time': std_time,
        'text': std_text
    }
    
    # Enhanced recognition
    start_time = time.time()
    enh_recognizer = EnhancedCardRecognizer()
    enh_card = enh_recognizer.recognize_card(img, debug)
    enh_time = (time.time() - start_time) * 1000
    
    if enh_card:
        enh_text = f"{enh_card.rank}{enh_card.suit} ({enh_card.confidence:.2f})"
    else:
        enh_text = "Failed"
    
    results['enhanced'] = {
        'card': enh_card,
        'time': enh_time,
        'text': enh_text
    }
    
    # Color detection
    start_time = time.time()
    detector = CardSuitColorDetector()
    color, color_conf = detector.detect_suit_color(img, debug)
    color_time = (time.time() - start_time) * 1000
    
    color_text = f"{color} ({color_conf:.2f})"
    
    results['color'] = {
        'color': color,
        'confidence': color_conf,
        'time': color_time,
        'text': color_text
    }
    
    # Log comparison
    logger.info(f"Comparison results for {image_name}:")
    logger.info(f"  Standard: {std_text} ({std_time:.0f}ms)")
    logger.info(f"  Enhanced: {enh_text} ({enh_time:.0f}ms)")
    logger.info(f"  Color: {color_text} ({color_time:.0f}ms)")
    
    # Check if the cards match
    if std_card and enh_card:
        match = std_card.rank == enh_card.rank and std_card.suit == enh_card.suit
        logger.info(f"  Match: {match}")
        
        # Check if the color is correct for the recognized suit
        if std_card.suit in ['h', 'd'] and color == 'red':
            logger.info("  Standard recognition color match: TRUE")
        elif std_card.suit in ['c', 's'] and color == 'black':
            logger.info("  Standard recognition color match: TRUE")
        else:
            logger.info("  Standard recognition color match: FALSE")
    
    # Save debug comparison
    if debug:
        debug_dir = "debug_comparison"
        os.makedirs(debug_dir, exist_ok=True)
        
        # Add method results as text on the image
        cv2.putText(display, f"Standard: {std_text}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(display, f"Time: {std_time:.0f}ms", (10, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)
        
        cv2.putText(display, f"Enhanced: {enh_text}", (10, 100), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(display, f"Time: {enh_time:.0f}ms", (10, 130), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
        
        cv2.putText(display, f"Color: {color_text}", (10, 170), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        cv2.putText(display, f"Time: {color_time:.0f}ms", (10, 200), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 1)
        
        # Save comparison image
        timestamp = int(time.time())
        output_path = f"{debug_dir}/comparison_{image_name.split('.')[0]}_{timestamp}.png"
        cv2.imwrite(output_path, display)
        logger.info(f"  Saved comparison to: {output_path}")
    
    return results

def test_directory(directory, method='compare', debug=False):
    """
    Test all images in a directory.
    
    Args:
        directory: Directory with card images
        method: Recognition method to use
        debug: Whether to save debug images
    """
    if not os.path.isdir(directory):
        logger.error(f"Directory not found: {directory}")
        return
    
    # Find all image files
    image_files = []
    for ext in ['.png', '.jpg', '.jpeg', '.bmp']:
        image_files.extend(Path(directory).glob(f"*{ext}"))
    
    logger.info(f"Found {len(image_files)} image files to process")
    
    results = {
        'standard_success': 0,
        'enhanced_success': 0,
        'total_images': len(image_files),
        'color_match_success': 0
    }
    
    for image_path in image_files:
        image_path = str(image_path)
        
        if method == 'standard':
            card = test_standard_recognition(image_path, debug)
            if card:
                results['standard_success'] += 1
                
        elif method == 'enhanced':
            card = test_enhanced_recognition(image_path, debug)
            if card:
                results['enhanced_success'] += 1
                
        elif method == 'color':
            color, confidence = test_color_recognition(image_path, debug)
            # No success tracking for color-only
            
        elif method == 'compare':
            comparison = compare_methods(image_path, debug)
            if comparison:
                if comparison['standard']['card']:
                    results['standard_success'] += 1
                if comparison['enhanced']['card']:
                    results['enhanced_success'] += 1
                
                # Check if the color matches the suit
                std_card = comparison['standard']['card']
                if std_card and comparison['color']['color'] != 'unknown':
                    if ((std_card.suit in ['h', 'd'] and comparison['color']['color'] == 'red') or
                        (std_card.suit in ['c', 's'] and comparison['color']['color'] == 'black')):
                        results['color_match_success'] += 1
    
    # Calculate success rates
    if results['total_images'] > 0:
        standard_rate = results['standard_success'] / results['total_images'] * 100
        enhanced_rate = results['enhanced_success'] / results['total_images'] * 100
        
        if results['standard_success'] > 0:
            color_match_rate = results['color_match_success'] / results['standard_success'] * 100
        else:
            color_match_rate = 0
        
        logger.info(f"Recognition results summary:")
        logger.info(f"  Total images: {results['total_images']}")
        logger.info(f"  Standard recognition success: {results['standard_success']} ({standard_rate:.1f}%)")
        logger.info(f"  Enhanced recognition success: {results['enhanced_success']} ({enhanced_rate:.1f}%)")
        logger.info(f"  Color matching success: {results['color_match_success']} ({color_match_rate:.1f}%)")
        
        # Improvement percentage
        if results['standard_success'] > 0:
            improvement = (results['enhanced_success'] - results['standard_success']) / results['standard_success'] * 100
            logger.info(f"  Improvement with enhanced recognition: {improvement:.1f}%")

def main():
    parser = argparse.ArgumentParser(description="Test enhanced card recognition")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--dir", default="debug_images", help="Directory with card images")
    parser.add_argument("--method", choices=["standard", "enhanced", "color", "compare"], default="compare", 
                       help="Recognition method to use")
    
    args = parser.parse_args()
    
    test_directory(args.dir, args.method, args.debug)

if __name__ == "__main__":
    main()
