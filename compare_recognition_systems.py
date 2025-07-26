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

# Import different recognition systems
try:
    from card_recognition_integration import CardRecognitionIntegration
    from enhanced_card_recognition import EnhancedCardRecognition
    from direct_card_recognition import DirectCardRecognition
except ImportError as e:
    print(f"Error importing recognition modules: {e}")
    print("Make sure all recognition systems are installed correctly.")
    exit(1)

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

def test_recognition_system(system_name, recognition_system, test_images, expected_values):
    """Test a recognition system on the provided test images."""
    results = {
        "system": system_name,
        "correct": 0,
        "incorrect": 0,
        "failed": 0,
        "times": [],
        "confidences": []
    }
    
    incorrect_details = []
    
    for i, (img_path, expected) in enumerate(zip(test_images, expected_values)):
        try:
            start_time = time.time()
            
            # Different systems have different APIs
            if system_name == "Template Matching":
                card, confidence = recognition_system.recognize_card(img_path)
            elif system_name == "Enhanced Recognition":
                card, confidence = recognition_system.recognize_card(img_path)
            elif system_name == "Direct Recognition":
                card, confidence = recognition_system.recognize_card_from_image(img_path)
            
            end_time = time.time()
            
            # Record results
            results["times"].append(end_time - start_time)
            results["confidences"].append(confidence)
            
            # Check if recognition was correct
            if card.lower() == expected.lower():
                results["correct"] += 1
            else:
                results["incorrect"] += 1
                incorrect_details.append({
                    "image": os.path.basename(img_path),
                    "expected": expected,
                    "recognized": card,
                    "confidence": confidence
                })
                
        except Exception as e:
            logger.error(f"Error processing {img_path} with {system_name}: {e}")
            results["failed"] += 1
    
    # Calculate metrics
    total = results["correct"] + results["incorrect"] + results["failed"]
    results["accuracy"] = results["correct"] / total if total > 0 else 0
    results["avg_time"] = np.mean(results["times"]) if results["times"] else 0
    results["avg_confidence"] = np.mean(results["confidences"]) if results["confidences"] else 0
    
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
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))
    
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
    parser = argparse.ArgumentParser(description="Compare card recognition systems")
    parser.add_argument("--skip-template", action="store_true", help="Skip testing the original template matching system")
    parser.add_argument("--skip-enhanced", action="store_true", help="Skip testing the enhanced recognition system")
    parser.add_argument("--skip-direct", action="store_true", help="Skip testing the direct recognition system")
    args = parser.parse_args()
    
    logger.info("Starting recognition system comparison")
    
    # Load test images
    test_images, expected_values = load_test_images()
    logger.info(f"Testing with {len(test_images)} images")
    
    results = []
    
    # Test original template matching
    if not args.skip_template:
        try:
            logger.info("Testing original template matching system...")
            template_system = CardRecognitionIntegration()
            template_results = test_recognition_system("Template Matching", template_system, test_images, expected_values)
            results.append(template_results)
        except Exception as e:
            logger.error(f"Failed to test template matching system: {e}")
    
    # Test enhanced recognition
    if not args.skip_enhanced:
        try:
            logger.info("Testing enhanced recognition system...")
            enhanced_system = EnhancedCardRecognition()
            enhanced_results = test_recognition_system("Enhanced Recognition", enhanced_system, test_images, expected_values)
            results.append(enhanced_results)
        except Exception as e:
            logger.error(f"Failed to test enhanced recognition system: {e}")
    
    # Test direct recognition
    if not args.skip_direct:
        try:
            logger.info("Testing direct recognition system...")
            direct_system = DirectCardRecognition()
            direct_results = test_recognition_system("Direct Recognition", direct_system, test_images, expected_values)
            results.append(direct_results)
        except Exception as e:
            logger.error(f"Failed to test direct recognition system: {e}")
    
    # Plot and save results
    if results:
        plot_results(results)
        logger.info("Comparison completed successfully")
    else:
        logger.error("No recognition systems were successfully tested")

if __name__ == "__main__":
    main()
