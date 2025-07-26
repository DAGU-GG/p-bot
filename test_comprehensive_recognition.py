"""
Test script for comprehensive card recognition.

This script tests the comprehensive card recognition system on sample images
and compares the results with the original recognizer.
"""

import os
import cv2
import logging
import argparse
import time
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('comprehensive_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('comprehensive_test')

def main():
    """Main function for the test script."""
    parser = argparse.ArgumentParser(description='Test comprehensive card recognition')
    parser.add_argument('--dir', default='debug_cards', help='Directory containing card images')
    parser.add_argument('--output', default='recognition_results/comprehensive', help='Output directory for results')
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Import recognizers
    try:
        from src.card_recognizer import CardRecognizer
        from comprehensive_card_recognition import ComprehensiveCardRecognizer
        
        # Create both recognizers
        original_recognizer = CardRecognizer()
        enhanced_recognizer = ComprehensiveCardRecognizer()
        
        logger.info("Successfully loaded both recognizers")
    except ImportError as e:
        logger.error(f"Failed to import recognizers: {e}")
        return
    
    # Find all card images
    image_dir = Path(args.dir)
    image_files = list(image_dir.glob('**/*.png'))
    logger.info(f"Found {len(image_files)} images to test")
    
    # Results containers
    results = {
        'original': {'correct': 0, 'incorrect': 0, 'errors': 0, 'empty_detected': 0},
        'enhanced': {'correct': 0, 'incorrect': 0, 'errors': 0, 'empty_detected': 0}
    }
    
    # Process each image
    for i, image_path in enumerate(image_files):
        logger.info(f"[{i+1}/{len(image_files)}] Processing {image_path}")
        
        # Load image
        image = cv2.imread(str(image_path))
        if image is None:
            logger.error(f"Failed to load image: {image_path}")
            continue
            
        # Get expected result from filename (if available)
        expected = None
        filename = image_path.name
        if '_' in filename:
            parts = filename.split('_')
            if len(parts) > 2 and parts[1] in ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']:
                if parts[2][0] in ['c', 'd', 'h', 's']:
                    expected = f"{parts[1]}{parts[2][0]}"
        
        # Run original recognizer
        try:
            start_time = time.time()
            original_card_code, original_confidence, original_method = original_recognizer.recognize_card(image, debug=False)
            original_time = time.time() - start_time
            
            logger.info(f"Original recognizer: {original_card_code} (confidence: {original_confidence:.2f}, method: {original_method}, time: {original_time:.3f}s)")
            
            if expected and original_card_code == expected:
                results['original']['correct'] += 1
            elif expected:
                results['original']['incorrect'] += 1
        except Exception as e:
            logger.error(f"Error in original recognizer: {e}")
            results['original']['errors'] += 1
            original_card_code = "error"
            original_confidence = 0.0
            original_method = "error"
            original_time = 0.0
        
        # Run enhanced recognizer
        try:
            start_time = time.time()
            enhanced_result = enhanced_recognizer.recognize_card(image, debug=True)
            enhanced_time = time.time() - start_time
            
            enhanced_card_code = enhanced_result['card_code']
            enhanced_confidence = enhanced_result.get('confidence', 0.0)
            enhanced_method = enhanced_result.get('method', 'unknown')
            enhanced_is_empty = enhanced_result.get('is_empty', False)
            
            logger.info(f"Enhanced recognizer: {enhanced_card_code} (confidence: {enhanced_confidence:.2f}, method: {enhanced_method}, is_empty: {enhanced_is_empty}, time: {enhanced_time:.3f}s)")
            
            if enhanced_is_empty:
                results['enhanced']['empty_detected'] += 1
            elif expected and enhanced_card_code == expected:
                results['enhanced']['correct'] += 1
            elif expected:
                results['enhanced']['incorrect'] += 1
        except Exception as e:
            logger.error(f"Error in enhanced recognizer: {e}")
            results['enhanced']['errors'] += 1
            enhanced_card_code = "error"
            enhanced_confidence = 0.0
            enhanced_method = "error"
            enhanced_time = 0.0
        
        # Write comparison result
        comparison_path = os.path.join(args.output, f"comparison_{image_path.stem}.txt")
        with open(comparison_path, 'w') as f:
            f.write(f"Image: {image_path}\n")
            f.write(f"Expected: {expected or 'unknown'}\n\n")
            f.write(f"Original Recognizer:\n")
            f.write(f"  Card: {original_card_code}\n")
            f.write(f"  Confidence: {original_confidence:.2f}\n")
            f.write(f"  Method: {original_method}\n")
            f.write(f"  Time: {original_time:.3f}s\n\n")
            f.write(f"Enhanced Recognizer:\n")
            f.write(f"  Card: {enhanced_card_code}\n")
            f.write(f"  Confidence: {enhanced_confidence:.2f}\n")
            f.write(f"  Method: {enhanced_method}\n")
            f.write(f"  Is Empty: {enhanced_is_empty}\n")
            f.write(f"  Time: {enhanced_time:.3f}s\n")
    
    # Print summary
    logger.info("\n--- RESULTS SUMMARY ---")
    logger.info("Original Recognizer:")
    logger.info(f"  Correct: {results['original']['correct']}")
    logger.info(f"  Incorrect: {results['original']['incorrect']}")
    logger.info(f"  Errors: {results['original']['errors']}")
    logger.info(f"  Empty Detected: {results['original']['empty_detected']}")
    
    logger.info("Enhanced Recognizer:")
    logger.info(f"  Correct: {results['enhanced']['correct']}")
    logger.info(f"  Incorrect: {results['enhanced']['incorrect']}")
    logger.info(f"  Errors: {results['enhanced']['errors']}")
    logger.info(f"  Empty Detected: {results['enhanced']['empty_detected']}")
    
    # Save summary
    summary_path = os.path.join(args.output, "summary.txt")
    with open(summary_path, 'w') as f:
        f.write("--- RESULTS SUMMARY ---\n")
        f.write("Original Recognizer:\n")
        f.write(f"  Correct: {results['original']['correct']}\n")
        f.write(f"  Incorrect: {results['original']['incorrect']}\n")
        f.write(f"  Errors: {results['original']['errors']}\n")
        f.write(f"  Empty Detected: {results['original']['empty_detected']}\n\n")
        
        f.write("Enhanced Recognizer:\n")
        f.write(f"  Correct: {results['enhanced']['correct']}\n")
        f.write(f"  Incorrect: {results['enhanced']['incorrect']}\n")
        f.write(f"  Errors: {results['enhanced']['errors']}\n")
        f.write(f"  Empty Detected: {results['enhanced']['empty_detected']}\n")
    
    logger.info(f"Results saved to {args.output}")

if __name__ == "__main__":
    main()
