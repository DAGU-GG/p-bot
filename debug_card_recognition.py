"""
Card Recognition Debug Tool
--------------------------
This tool helps diagnose card recognition issues by:
1. Running card recognition on sample images or live screen capture
2. Showing each stage of the recognition process
3. Displaying detailed debug information
4. Saving debug images for analysis

Usage:
    python debug_card_recognition.py [--image PATH_TO_IMAGE] [--live]
    
    --image: Path to a card image for testing
    --live: Use live screen capture
"""

import os
import sys
import time
import argparse
import logging
import numpy as np
import cv2
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from card_recognizer import CardRecognizer
from community_card_detector import CommunityCardDetector
from region_loader import RegionLoader
from window_capture import PokerStarsWindowCapture

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug_card_recognition.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('debug_card_recognition')

class CardRecognitionDebugger:
    def __init__(self):
        self.card_recognizer = CardRecognizer()
        self.region_loader = RegionLoader()
        self.community_card_detector = CommunityCardDetector(self.card_recognizer)
        self.window_capture = PokerStarsWindowCapture()  # Initialize poker stars window capture
        
        # Ensure debug directories exist
        os.makedirs('debug_images', exist_ok=True)
        os.makedirs('debug_cards', exist_ok=True)
        os.makedirs('debug_community', exist_ok=True)
        
        # Store preprocessing variants
        self.preprocessing_variants = []
        
    def debug_single_image(self, image_path):
        """Debug card recognition on a single image."""
        if not os.path.exists(image_path):
            logger.error(f"Image not found: {image_path}")
            return
            
        logger.info(f"Debugging card recognition for image: {image_path}")
        
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            logger.error(f"Failed to load image: {image_path}")
            return
            
        # Process image
        self._process_and_display(image, os.path.basename(image_path))
    
    def debug_live_capture(self):
        """Debug card recognition using live screen capture."""
        logger.info("Starting live card recognition debugging")
        
        try:
            # Capture screen
            screen = self.window_capture.capture_window()
            if screen is None:
                logger.error("Failed to capture window")
                return
                
            timestamp = int(time.time())
            
            # Save captured screen
            cv2.imwrite(f"debug_images/capture_{timestamp}.png", screen)
            
            # Process captured screen
            self._process_and_display(screen, f"live_capture_{timestamp}")
            
        except Exception as e:
            logger.exception(f"Error in live capture debug: {e}")
    
    def _process_and_display(self, image, image_name):
        """Process an image through all recognition steps and display debug info."""
        timestamp = int(time.time())
        
        # Make sure region loader is initialized
        if not hasattr(self, 'region_loader') or self.region_loader is None:
            self.region_loader = RegionLoader()
            logger.info("Initializing RegionLoader")
        
        # 1. Extract card regions from image
        # Check if regions exist, if not, show an error
        if not self.region_loader.regions_exist():
            logger.error("No saved regions found! Please calibrate regions first.")
            # Create a visual indicator
            error_image = np.zeros((400, 600, 3), dtype=np.uint8)
            cv2.putText(error_image, "ERROR: No regions found!", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.putText(error_image, "Please calibrate regions first", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.putText(error_image, "Use the UI Region Calibrator", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.imshow("Region Error", error_image)
            cv2.waitKey(5000)
            return

        # Load regions after verifying they exist
        regions = self.region_loader.get_community_card_regions()
        
        # Extract each card region
        card_images = []
        for i, region in enumerate(regions):
            try:
                x, y, w, h = region
                card_img = image[y:y+h, x:x+w]
                card_images.append((f"Community Card {i+1}", card_img))
                
                # Save extracted card region
                cv2.imwrite(f"debug_cards/card_region_{i+1}_{timestamp}.png", card_img)
            except Exception as e:
                logger.error(f"Error extracting card region {i+1}: {e}")
        
        # Add hero cards if available
        hero_regions = self.region_loader.get_hero_card_regions()
        for i, region in enumerate(hero_regions):
            try:
                x, y, w, h = region
                card_img = image[y:y+h, x:x+w]
                card_images.append((f"Hero Card {i+1}", card_img))
                
                # Save extracted card region
                cv2.imwrite(f"debug_cards/card_hero_card{i+1}_{timestamp}.png", card_img)
            except Exception as e:
                logger.error(f"Error extracting hero card region {i+1}: {e}")
        
        # 2. Process each card
        if not card_images:
            logger.warning("No card images extracted. Check if the image contains valid card regions.")
            plt.figure(figsize=(10, 5))
            plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            plt.title("Input Image - No Cards Detected")
            plt.savefig(f"debug_images/no_cards_detected_{timestamp}.png")
            plt.show()
            return
            
        fig = plt.figure(figsize=(20, 5 * len(card_images)))
        gs = GridSpec(len(card_images), 4, figure=fig)
        
        recognition_results = []
        
        for idx, (card_name, card_img) in enumerate(card_images):
            if card_img is None or card_img.size == 0:
                logger.warning(f"Empty card image for {card_name}")
                continue
                
            # Check if card is present
            is_present = self.community_card_detector._is_card_present(card_img)
            
            # Process card for recognition if present
            if is_present:
                # Get preprocessing variants
                self.preprocessing_variants = []
                preprocessed = self.card_recognizer.preprocess_card_image(card_img, collect_variants=True)
                variants = [("Original", card_img)] + self.preprocessing_variants
                
                # Recognize card
                card_value, confidence, method = self.card_recognizer.recognize_card(card_img, debug=True)
                
                # Get template matching results if available
                template_results = getattr(self.card_recognizer, 'debug_template_results', [])
                
                recognition_results.append({
                    'card_name': card_name,
                    'is_present': is_present,
                    'card_value': card_value,
                    'confidence': confidence,
                    'method': method,
                    'template_results': template_results[:5] if template_results else []  # Top 5 matches
                })
                
                # Display original card
                ax1 = fig.add_subplot(gs[idx, 0])
                ax1.imshow(cv2.cvtColor(card_img, cv2.COLOR_BGR2RGB))
                ax1.set_title(f"{card_name}\nRecognized as: {card_value}\nConfidence: {confidence:.2f}\nMethod: {method}")
                ax1.axis('off')
                
                # Display preprocessing variants
                ax2 = fig.add_subplot(gs[idx, 1])
                if len(variants) > 1:
                    # Create a grid of preprocessing variants
                    rows = int(np.ceil(len(variants) / 2))
                    cols = min(2, len(variants))
                    variant_img = np.zeros((rows * 100, cols * 100, 3), dtype=np.uint8)
                    
                    for i, (var_name, var_img) in enumerate(variants):
                        r, c = i // cols, i % cols
                        if len(var_img.shape) == 2:  # Grayscale
                            var_img_color = cv2.cvtColor(var_img, cv2.COLOR_GRAY2BGR)
                        else:
                            var_img_color = var_img.copy()
                        
                        # Resize to fit in grid
                        var_img_resized = cv2.resize(var_img_color, (100, 100))
                        
                        # Put in grid
                        variant_img[r*100:(r+1)*100, c*100:(c+1)*100] = var_img_resized
                        
                        # Add label
                        cv2.putText(variant_img, var_name, (c*100+5, r*100+15), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                    
                    ax2.imshow(cv2.cvtColor(variant_img, cv2.COLOR_BGR2RGB))
                else:
                    ax2.imshow(cv2.cvtColor(card_img, cv2.COLOR_BGR2RGB))
                ax2.set_title("Preprocessing Variants")
                ax2.axis('off')
                
                # Display template matching results
                ax3 = fig.add_subplot(gs[idx, 2])
                if template_results:
                    # Create a grid of top template matches
                    rows = min(3, len(template_results))
                    template_img = np.zeros((rows * 120, 250, 3), dtype=np.uint8)
                    
                    for i, (template_name, score, template) in enumerate(template_results[:rows]):
                        if template is not None:
                            # Resize template to fit
                            template_resized = cv2.resize(template, (100, 100))
                            if len(template_resized.shape) == 2:  # Grayscale
                                template_resized = cv2.cvtColor(template_resized, cv2.COLOR_GRAY2BGR)
                            
                            # Add to grid
                            template_img[i*120:i*120+100, 0:100] = template_resized
                            
                            # Add text
                            text = f"{template_name}: {score:.3f}"
                            cv2.putText(template_img, text, (105, i*120+50), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    
                    ax3.imshow(cv2.cvtColor(template_img, cv2.COLOR_BGR2RGB))
                else:
                    ax3.text(0.5, 0.5, "No template matches", 
                             horizontalalignment='center', verticalalignment='center')
                ax3.set_title("Top Template Matches")
                ax3.axis('off')
                
                # Display color analysis
                ax4 = fig.add_subplot(gs[idx, 3])
                try:
                    # Extract dominant colors
                    card_img_small = cv2.resize(card_img, (50, 50))
                    pixels = card_img_small.reshape(-1, 3)
                    
                    # Count colors for histogram
                    red_pixels = np.sum((pixels[:, 2] > 120) & (pixels[:, 0] < 100) & (pixels[:, 1] < 100))
                    black_pixels = np.sum((pixels < 80).all(axis=1))
                    white_pixels = np.sum((pixels > 200).all(axis=1))
                    
                    # Create color histogram
                    colors = ['Red', 'Black', 'White', 'Other']
                    counts = [red_pixels, black_pixels, white_pixels, 
                              pixels.shape[0] - (red_pixels + black_pixels + white_pixels)]
                    
                    ax4.bar(colors, counts, color=['red', 'black', 'lightgray', 'blue'])
                    ax4.set_title("Color Analysis")
                    
                    # Add text with percentages
                    total = sum(counts)
                    for i, (color, count) in enumerate(zip(colors, counts)):
                        percentage = count / total * 100 if total > 0 else 0
                        ax4.text(i, count + 5, f"{percentage:.1f}%", 
                                 ha='center', va='bottom', fontsize=8)
                    
                    # Add suit type prediction
                    red_percentage = red_pixels / total * 100 if total > 0 else 0
                    black_percentage = black_pixels / total * 100 if total > 0 else 0
                    
                    if red_percentage > 5:
                        suit_prediction = "Red suit (Hearts/Diamonds)"
                    elif black_percentage > 5:
                        suit_prediction = "Black suit (Clubs/Spades)"
                    else:
                        suit_prediction = "Uncertain"
                        
                    ax4.text(0.5, -0.1, f"Suit prediction: {suit_prediction}", 
                             transform=ax4.transAxes, ha='center', fontsize=10)
                    
                except Exception as e:
                    logger.error(f"Error in color analysis: {e}")
                    ax4.text(0.5, 0.5, "Color analysis error", 
                             horizontalalignment='center', verticalalignment='center')
            else:
                # Card not present
                recognition_results.append({
                    'card_name': card_name,
                    'is_present': False,
                    'card_value': None,
                    'confidence': 0,
                    'method': 'None'
                })
                
                # Display empty slot
                ax = fig.add_subplot(gs[idx, :])
                ax.imshow(cv2.cvtColor(card_img, cv2.COLOR_BGR2RGB))
                ax.set_title(f"{card_name} - No card detected")
                ax.axis('off')
        
        # Save figure
        plt.tight_layout()
        plt.savefig(f"debug_images/recognition_debug_{timestamp}.png")
        plt.close()
        
        # Print summary
        logger.info("Recognition Summary:")
        for result in recognition_results:
            if result['is_present']:
                logger.info(f"{result['card_name']}: {result['card_value']} "
                           f"(Confidence: {result['confidence']:.2f}, Method: {result['method']})")
            else:
                logger.info(f"{result['card_name']}: No card detected")
                
        return recognition_results

def main():
    parser = argparse.ArgumentParser(description='Debug card recognition')
    parser.add_argument('--image', help='Path to card image for testing')
    parser.add_argument('--live', action='store_true', help='Use live screen capture')
    
    args = parser.parse_args()
    
    debugger = CardRecognitionDebugger()
    
    if args.image:
        debugger.debug_single_image(args.image)
    elif args.live:
        debugger.debug_live_capture()
    else:
        # If no arguments, use live capture
        debugger.debug_live_capture()
        
    logger.info("Debug complete. Check debug_images directory for results.")

if __name__ == "__main__":
    main()
