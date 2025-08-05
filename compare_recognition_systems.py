"""
Performance comparison between card recognition systems.

This script compares the performance of different card recognition approaches:
- Template matching (original)
- Enhanced recognition (improved template matching)
- Direct recognition (color analysis + shape/text detection)

Each system is tested on the same set of test images, and metrics are recorded:
- Accuracy (correct recognitions / total attempts)
- Speed (average recognition time)
- Confidence (average confidence score)
"""

import os
import time
import logging
import argparse
import matplotlib.pyplot as plt
import numpy as np
from tabulate import tabulate

# Import OpenCV for image processing
try:
    import cv2
except ImportError:
    cv2 = None
    print("Warning: OpenCV not available, some features may not work")

# Constants for recognition system names
TEMPLATE_MATCHING = "Template Matching"
ENHANCED_RECOGNITION = "Enhanced Recognition"
DIRECT_RECOGNITION = "Direct Recognition"

# Import different recognition systems
try:
    from hardware_capture_integration import HardwareCaptureSystem, HardwareCaptureConfig
    from enhanced_ocr_recognition import EnhancedOCRCardRecognition
    from fallback_card_recognition import FallbackCardRecognition
except ImportError as e:
    print(f"Warning: Some recognition modules not available: {e}")
    print("Will continue with available systems.")

# Try to import optional systems
try:
    from card_recognition_integration import CardRecognitionIntegration
except ImportError:
    CardRecognitionIntegration = None

try:
    from enhanced_card_recognition import EnhancedCardRecognition
except ImportError:
    EnhancedCardRecognition = None

try:
    from direct_card_recognition import DirectCardRecognition
except ImportError:
    DirectCardRecognition = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("recognition_comparison.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("recognition_comparison")

def load_test_images():
    """Load test images from the debug_cards directory."""
    test_images = []
    expected_values = []
    
    # Test folders - each subfolder named after the expected card value
    test_folders = [
        "debug_cards",
        "debug_community",
        "debug_color_detection"
    ]
    
    for folder in test_folders:
        if not os.path.exists(folder):
            logger.warning(f"Test folder {folder} not found. Skipping.")
            continue
            
        # Each subfolder is named after the card it contains
        for card_folder in os.listdir(folder):
            card_path = os.path.join(folder, card_folder)
            if not os.path.isdir(card_path):
                continue
                
            # Card value is the folder name
            card_value = card_folder.lower()
            
            # Find all images in this folder
            for img_file in os.listdir(card_path):
                if img_file.endswith(('.png', '.jpg', '.jpeg')):
                    img_path = os.path.join(card_path, img_file)
                    test_images.append(img_path)
                    expected_values.append(card_value)
    
    logger.info(f"Loaded {len(test_images)} test images from {len(set(expected_values))} unique cards")
    return test_images, expected_values

def test_hardware_capture_recognition():
    """Test recognition systems with live hardware capture"""
    logger.info("Testing Hardware Capture Recognition...")
    
    try:
        # Initialize hardware capture system
        config = HardwareCaptureConfig(debug_mode=True)
        capture_system = HardwareCaptureSystem(config)
        
        # Test OBS window detection
        obs_window = capture_system.find_obs_window()
        if not obs_window:
            logger.error("OBS Studio window not found. Make sure OBS is running with UGREEN capture card configured.")
            return None
        
        logger.info(f"Found OBS window: {obs_window.title}")
        
        # Capture screenshot from hardware
        screenshot = capture_system.capture_obs_window()
        if screenshot is None:
            logger.error("Failed to capture from OBS window")
            return None
        
        logger.info(f"Hardware capture successful: {screenshot.shape}")
        if cv2 is not None:
            cv2.imwrite("hardware_capture_test.png", screenshot)
        else:
            logger.warning("OpenCV not available, cannot save screenshot")
        
        # Auto-calibrate regions
        if not capture_system.auto_calibrate_from_hardware():
            logger.warning("Auto-calibration failed, using manual regions if available")
        
        # Test recognition on captured frame
        game_state = capture_system.analyze_current_frame()
        
        if game_state:
            logger.info("Hardware capture recognition results:")
            logger.info(f"  Hero cards: {game_state.get('hero_cards', [])}")
            logger.info(f"  Community cards: {game_state.get('community_cards', [])}")
            logger.info(f"  Analysis confidence: {game_state.get('analysis_confidence', 0):.2f}")
            
            # Generate advice
            advice = capture_system.get_poker_advice(game_state)
            logger.info(f"  Recommended action: {advice['action']} ({advice['confidence']:.2f})")
            logger.info(f"  Reasoning: {advice['reasoning']}")
            
            return {
                'system': 'Hardware Capture',
                'game_state': game_state,
                'advice': advice,
                'screenshot_saved': 'hardware_capture_test.png'
            }
        else:
            logger.warning("Hardware capture analysis returned no results")
            return None
            
    except Exception as e:
        logger.error(f"Hardware capture test failed: {e}")
        return None

def test_recognition_system(system_name, recognition_system, test_images, expected_values):
    """Test a recognition system on the provided test images."""
    results = _initialize_test_results(system_name)
    incorrect_details = []
    
    for i, (img_path, expected) in enumerate(zip(test_images, expected_values)):
        test_result = _test_single_image(system_name, recognition_system, img_path, expected)
        _update_results(results, test_result, incorrect_details, img_path, expected)
    
    # Calculate metrics
    _calculate_final_metrics(results)
    _log_results(system_name, results, incorrect_details)
    
    return results

def _initialize_test_results(system_name):
    """Initialize empty results structure"""
    return {
        "system": system_name,
        "correct": 0,
        "incorrect": 0,
        "failed": 0,
        "times": [],
        "confidences": []
    }

def _test_single_image(system_name, recognition_system, img_path, expected):
    """Test recognition on a single image"""
    try:
        start_time = time.time()
        card, confidence = _call_recognition_method(system_name, recognition_system, img_path)
        end_time = time.time()
        
        return {
            'success': True,
            'card': card,
            'confidence': confidence,
            'time': end_time - start_time,
            'correct': card.lower() == expected.lower()
        }
        
    except Exception as e:
        logger.error(f"Error processing {img_path} with {system_name}: {e}")
        return {'success': False}

def _call_recognition_method(system_name, recognition_system, img_path):
    """Call the appropriate recognition method for the system"""
    # Load image as numpy array for most systems
    if cv2 is not None:
        img = cv2.imread(img_path)
        if img is None:
            raise ValueError(f"Could not load image: {img_path}")
    else:
        raise ImportError("OpenCV not available for image loading")
    
    if system_name == TEMPLATE_MATCHING:
        # If this system expects a file path, use the path directly
        try:
            return recognition_system.recognize_card(img_path)
        except:
            # If it expects numpy array, use the loaded image
            result = recognition_system.recognize_card(img)
            if hasattr(result, 'rank') and hasattr(result, 'suit'):
                return f"{result.rank}{result.suit}", result.confidence
            return result
    elif system_name == ENHANCED_RECOGNITION:
        result = recognition_system.recognize_card(img)
        if result and hasattr(result, 'rank') and hasattr(result, 'suit'):
            return f"{result.rank}{result.suit}", result.confidence
        return "unknown", 0.0
    elif system_name == DIRECT_RECOGNITION:
        # Handle both file path and numpy array interfaces
        try:
            return recognition_system.recognize_card_from_image(img_path)
        except:
            result = recognition_system.recognize_card(img)
            if hasattr(result, 'rank') and hasattr(result, 'suit'):
                return f"{result.rank}{result.suit}", result.confidence
            return result
    else:
        raise ValueError(f"Unknown recognition system: {system_name}")

def _update_results(results, test_result, incorrect_details, img_path, expected):
    """Update results with single test outcome"""
    if not test_result['success']:
        results["failed"] += 1
        return
    
    # Record timing and confidence
    results["times"].append(test_result['time'])
    results["confidences"].append(test_result['confidence'])
    
    # Check correctness
    if test_result['correct']:
        results["correct"] += 1
    else:
        results["incorrect"] += 1
        incorrect_details.append({
            "image": os.path.basename(img_path),
            "expected": expected,
            "recognized": test_result['card'],
            "confidence": test_result['confidence']
        })

def _calculate_final_metrics(results):
    """Calculate final accuracy and average metrics"""
    total = results["correct"] + results["incorrect"] + results["failed"]
    results["accuracy"] = results["correct"] / total if total > 0 else 0
    results["avg_time"] = np.mean(results["times"]) if results["times"] else 0
    results["avg_confidence"] = np.mean(results["confidences"]) if results["confidences"] else 0

def _log_results(system_name, results, incorrect_details):
    """Log detailed results"""
    logger.info(f"{system_name} Results:")
    logger.info(f"  Accuracy: {results['accuracy']:.2%}")
    logger.info(f"  Average Time: {results['avg_time']:.4f} seconds")
    logger.info(f"  Average Confidence: {results['avg_confidence']:.4f}")
    
    if incorrect_details:
        logger.info(f"  Incorrect Recognitions ({len(incorrect_details)}):")
        for detail in incorrect_details[:10]:  # Limit to first 10 for readability
            logger.info(f"    {detail['image']}: Expected {detail['expected']}, Got {detail['recognized']} (Confidence: {detail['confidence']:.2f})")
        if len(incorrect_details) > 10:
            logger.info(f"    ... and {len(incorrect_details) - 10} more")
    
    return results

def plot_results(results):
    """Generate comparison charts for the results."""
    systems = [r["system"] for r in results]
    accuracies = [r["accuracy"] for r in results]
    times = [r["avg_time"] for r in results]
    confidences = [r["avg_confidence"] for r in results]
    
    # Create figure with subplots
    _, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))
    
    # Plot accuracy
    ax1.bar(systems, accuracies, color=['blue', 'green', 'red'])
    ax1.set_title('Recognition Accuracy')
    ax1.set_ylabel('Accuracy (%)')
    ax1.set_ylim(0, 1)
    ax1.set_yticks(np.arange(0, 1.1, 0.1))
    ax1.set_yticklabels([f'{x:.0%}' for x in np.arange(0, 1.1, 0.1)])
    
    # Plot time
    ax2.bar(systems, times, color=['blue', 'green', 'red'])
    ax2.set_title('Average Recognition Time')
    ax2.set_ylabel('Time (seconds)')
    
    # Plot confidence
    ax3.bar(systems, confidences, color=['blue', 'green', 'red'])
    ax3.set_title('Average Confidence Score')
    ax3.set_ylabel('Confidence')
    ax3.set_ylim(0, 1)
    
    plt.tight_layout()
    plt.savefig('recognition_comparison.png')
    logger.info("Comparison chart saved as 'recognition_comparison.png'")
    
    # Create a table for the README
    table_data = []
    for r in results:
        table_data.append([
            r["system"],
            f"{r['accuracy']:.2%}",
            f"{r['avg_time']:.4f}s",
            f"{r['avg_confidence']:.4f}"
        ])
    
    table_headers = ["System", "Accuracy", "Avg. Time", "Avg. Confidence"]
    table = tabulate(table_data, headers=table_headers, tablefmt="pipe")
    
    with open("recognition_comparison_results.md", "w") as f:
        f.write("# Card Recognition System Comparison\n\n")
        f.write(table)
        f.write("\n\n")
        f.write("![Comparison Chart](recognition_comparison.png)\n")
    
    logger.info("Detailed results saved to 'recognition_comparison_results.md'")

def main():
    """Main function to compare recognition systems"""
    args = _parse_arguments()
    logger.info("Starting recognition system comparison")
    
    # Handle hardware testing
    if args.test_hardware or args.hardware_only:
        hardware_success = _test_hardware_capture(args.hardware_only)
        if args.hardware_only:
            return
        if not hardware_success and args.hardware_only:
            return
    
    # Run traditional system tests
    _run_traditional_system_tests(args)

def _parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Compare card recognition systems")
    parser.add_argument("--skip-template", action="store_true", help="Skip testing the original template matching system")
    parser.add_argument("--skip-enhanced", action="store_true", help="Skip testing the enhanced recognition system")
    parser.add_argument("--skip-direct", action="store_true", help="Skip testing the direct recognition system")
    parser.add_argument("--test-hardware", action="store_true", help="Test hardware capture system (requires OBS with UGREEN capture card)")
    parser.add_argument("--hardware-only", action="store_true", help="Only test hardware capture system")
    return parser.parse_args()

def _test_hardware_capture(hardware_only):
    """Test hardware capture system"""
    logger.info("Testing hardware capture system...")
    hardware_result = test_hardware_capture_recognition()
    
    if hardware_result:
        logger.info("Hardware capture test completed successfully")
        if hardware_only:
            logger.info("Hardware-only test completed")
        return True
    else:
        logger.error("Hardware capture test failed")
        return False

def _run_traditional_system_tests(args):
    """Run tests for traditional recognition systems"""
    test_images, expected_values = load_test_images()
    logger.info(f"Testing with {len(test_images)} images")
    
    results = []
    
    # Test each system based on arguments
    _test_template_matching(args, results, test_images, expected_values)
    _test_enhanced_recognition(args, results, test_images, expected_values)
    _test_direct_recognition(args, results, test_images, expected_values)
    
    # Generate results
    if results:
        plot_results(results)
        logger.info("Comparison complete!")
    else:
        logger.info("No systems were tested")

def _test_template_matching(args, results, test_images, expected_values):
    """Test template matching system if not skipped"""
    if not args.skip_template:
        if CardRecognitionIntegration is not None:
            try:
                logger.info("Testing original template matching system...")
                template_system = CardRecognitionIntegration()
                template_results = test_recognition_system(TEMPLATE_MATCHING, template_system, test_images, expected_values)
                results.append(template_results)
            except Exception as e:
                logger.error(f"Failed to test template matching system: {e}")
        else:
            logger.warning("CardRecognitionIntegration not available, skipping template matching test")

def _test_enhanced_recognition(args, results, test_images, expected_values):
    """Test enhanced recognition system if not skipped"""
    if not args.skip_enhanced:
        if EnhancedCardRecognition is not None:
            try:
                logger.info("Testing enhanced recognition system...")
                enhanced_system = EnhancedCardRecognition()
                enhanced_results = test_recognition_system(ENHANCED_RECOGNITION, enhanced_system, test_images, expected_values)
                results.append(enhanced_results)
            except Exception as e:
                logger.error(f"Failed to test enhanced recognition system: {e}")
        else:
            # Fallback to OCR-based enhanced recognition
            try:
                logger.info("Testing enhanced OCR recognition system...")
                enhanced_system = EnhancedOCRCardRecognition()
                enhanced_results = test_recognition_system(ENHANCED_RECOGNITION, enhanced_system, test_images, expected_values)
                results.append(enhanced_results)
            except Exception as e:
                logger.error(f"Failed to test enhanced OCR recognition system: {e}")
                logger.warning("Enhanced recognition not available")

def _test_direct_recognition(args, results, test_images, expected_values):
    """Test direct recognition system if not skipped"""
    if not args.skip_direct:
        if DirectCardRecognition is not None:
            try:
                logger.info("Testing direct recognition system...")
                direct_system = DirectCardRecognition()
                direct_results = test_recognition_system(DIRECT_RECOGNITION, direct_system, test_images, expected_values)
                results.append(direct_results)
            except Exception as e:
                logger.error(f"Failed to test direct recognition system: {e}")
        else:
            # Fallback to fallback card recognition
            try:
                logger.info("Testing fallback recognition system...")
                fallback_system = FallbackCardRecognition()
                fallback_results = test_recognition_system(DIRECT_RECOGNITION, fallback_system, test_images, expected_values)
                results.append(fallback_results)
            except Exception as e:
                logger.error(f"Failed to test fallback recognition system: {e}")
                logger.warning("Direct recognition not available")

if __name__ == "__main__":
    main()
