"""
PokerStars Bot - Stage 3: Card Recognition System
This module handles recognition of player hole cards using template matching and OCR.
Designed specifically for 9-player PokerStars tables.
"""

import cv2
import numpy as np
import os
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import time
from PIL import Image

# Add the parent directory to the path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import RegionLoader
try:
    from src.region_loader import RegionLoader
except ImportError:
    # Fallback implementation if needed
    class RegionLoader:
        def __init__(self):
            self.regions = {}
        
        def load_regions(self, config_path=None):
            return self.regions

# Optional OCR import
try:
    import pytesseract
    # Configure Tesseract path for Windows
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    print("Warning: pytesseract not available, OCR functionality disabled")

@dataclass
class Card:
    """Represents a playing card with rank and suit."""
    rank: str  # '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A'
    suit: str  # 'h', 'd', 'c', 's' (hearts, diamonds, clubs, spades)
    confidence: float = 0.0
    
    def __str__(self):
        suit_names = {'h': 'Hearts', 'd': 'Diamonds', 'c': 'Clubs', 's': 'Spades'}
        rank_names = {
            '2': 'Two', '3': 'Three', '4': 'Four', '5': 'Five', '6': 'Six',
            '7': 'Seven', '8': 'Eight', '9': 'Nine', 'T': 'Ten',
            'J': 'Jack', 'Q': 'Queen', 'K': 'King', 'A': 'Ace'
        }
        return f"{rank_names.get(self.rank, self.rank)} of {suit_names.get(self.suit, self.suit)}"

@dataclass
class HoleCards:
    """Represents the player's two hole cards."""
    card1: Optional[Card] = None
    card2: Optional[Card] = None
    detection_confidence: float = 0.0
    timestamp: float = 0.0
    
    def is_valid(self) -> bool:
        """Check if both cards are detected with reasonable confidence."""
        return (self.card1 is not None and self.card2 is not None and 
                self.card1.confidence > 0.6 and self.card2.confidence > 0.6)
    
    def __str__(self):
        if not self.is_valid():
            return "No cards detected"
        return f"{self.card1}, {self.card2}"

class CardRecognizer:
    """
    Handles recognition of playing cards from PokerStars table screenshots.
    Uses template matching and OCR for robust card identification.
    """
    
    def __init__(self):
        """Initialize the card recognizer with templates and settings."""
        self.logger = logging.getLogger(__name__)
        
        # Card recognition settings
        self.template_match_threshold = 0.7
        self.ocr_confidence_threshold = 60
        
        # Card templates storage
        self.card_templates = {}
        self.template_loaded = False
        
        # Load regions from saved configuration
        try:
            from src.region_loader import RegionLoader
        except ImportError:
            # Define a minimal Region class if the import fails
            class Region:
                def __init__(self, x=0, y=0, width=0, height=0, name=""):
                    self.x = x
                    self.y = y
                    self.width = width
                    self.height = height
                    self.name = name
            
            # Define a minimal RegionLoader class
            class RegionLoader:
                def __init__(self):
                    self.regions = {
                        "hero_card1": Region(100, 100, 50, 70, "hero_card1"),
                        "hero_card2": Region(160, 100, 50, 70, "hero_card2")
                    }
                
                def load_regions(self, config_path=None):
                    return self.regions
        self.region_loader = RegionLoader()
        self.card_regions = self.region_loader.get_hero_card_regions()
        
        # Log what regions we loaded with exact coordinates
        if self.card_regions:
            self.logger.info(f"CardRecognizer loaded {len(self.card_regions)} saved hero card regions:")
            for name, region in self.card_regions.items():
                self.logger.info(f"   {name}: x={region['x_percent']:.4f}, y={region['y_percent']:.4f}, "
                               f"w={region['width_percent']:.4f}, h={region['height_percent']:.4f}")
        else:
            # Fallback to defaults only if no saved regions exist
            self.card_regions = self._define_card_regions()
            self.logger.warning("⚠️ No saved hero card regions found, using defaults")
        
        # PokerStars specific settings for 9-player tables
        self.hero_position = 0  # Bottom center position
        
        # Create directories
        os.makedirs("card_templates", exist_ok=True)
        os.makedirs("debug_cards", exist_ok=True)
        
        # Load or create card templates
        self._initialize_templates()
        
        self.logger.info("Card recognizer initialized for 9-player PokerStars tables")
    
    def update_regions(self, new_regions: Dict[str, Dict]):
        """Update hero card regions dynamically."""
        self.card_regions.update(new_regions)
        self.logger.info(f"Updated hero card regions: {len(new_regions)} regions loaded")
    
    def _define_default_regions(self) -> Dict[str, Dict]:
        """This method is deprecated - regions should only come from RegionLoader."""
        self.logger.warning("❌ Using hardcoded fallback regions - Please calibrate regions!")
        return {}  # Return empty - no more hardcoded regions
    
    def _initialize_templates(self):
        """Initialize card templates for recognition."""
        try:
            # Check if templates exist
            template_dir = "card_templates"
            if os.path.exists(template_dir) and len(os.listdir(template_dir)) > 0:
                self._load_existing_templates()
            else:
                self._create_template_placeholders()
                
        except Exception as e:
            self.logger.error(f"Error initializing templates: {e}")
    
    def _load_existing_templates(self):
        """Load existing card templates from disk."""
        try:
            template_dir = "card_templates"
            # Map actual file names to internal representation
            rank_mapping = {
                '2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7', '8': '8', '9': '9',
                '10': 'T', 'J': 'J', 'Q': 'Q', 'K': 'K', 'A': 'A'
            }
            suit_mapping = {
                'hearts': 'h', 'diamonds': 'd', 'clubs': 'c', 'spades': 's'
            }
            
            loaded_count = 0
            # Load templates using actual file naming convention
            for file_rank, internal_rank in rank_mapping.items():
                for file_suit, internal_suit in suit_mapping.items():
                    template_file = os.path.join(template_dir, f"{file_rank}_{file_suit}.png")
                    if os.path.exists(template_file):
                        # Read template in color first to check if it exists
                        color_template = cv2.imread(template_file)
                        if color_template is not None:
                            # Convert to grayscale for processing
                            template = cv2.cvtColor(color_template, cv2.COLOR_BGR2GRAY)
                            # Store both color and grayscale versions
                            template_key = f"{internal_rank}{internal_suit}"
                            self.card_templates[template_key] = template
                            # Also store color version for debugging
                            self.logger.debug(f"Loaded template: {template_key} from {template_file}")
                            loaded_count += 1
            
            if loaded_count > 0:
                self.template_loaded = True
                self.logger.info(f"Loaded {loaded_count} card templates")
            else:
                self.logger.warning("No valid card templates found")
                
        except Exception as e:
            self.logger.error(f"Error loading templates: {e}")
    
    def _create_template_placeholders(self):
        """Create placeholder templates and instructions for manual collection."""
        try:
            template_dir = "card_templates"
            
            # Create instruction file
            instructions = """
Card Template Collection Instructions:
=====================================

Your card templates are already set up! The bot now supports your naming format:

Current naming convention detected: rank_suit.png format
- 2_clubs.png, 3_hearts.png, K_spades.png, A_diamonds.png, 10_hearts.png

The bot automatically maps these to internal format for recognition.
Top-half card templates are fully supported for recognition.

Required files:
Ranks: 2, 3, 4, 5, 6, 7, 8, 9, 10, J, Q, K, A
Suits: hearts, diamonds, clubs, spades

Expected template files:
"""
            
            # List actual expected file names
            ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
            suits = ['hearts', 'diamonds', 'clubs', 'spades']
            
            for rank in ranks:
                for suit in suits:
                    instructions += f"- {rank}_{suit}.png\n"
            
            instructions += """
Tips:
- Crop cards to show just the card face (no background)
- Keep consistent sizing (recommended: 60x80 pixels)
- Use PNG format for transparency support
- Ensure good contrast and clarity

Once templates are collected, restart the bot to load them.
"""
            
            with open(os.path.join(template_dir, "INSTRUCTIONS.txt"), 'w') as f:
                f.write(instructions)
            
            self.logger.info("Created template collection instructions")
            
        except Exception as e:
            self.logger.error(f"Error creating template placeholders: {e}")
    
    def extract_hero_cards_region(self, table_image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Extract the regions containing hero's hole cards."""
        try:
            height, width = table_image.shape[:2]
            self.logger.debug(f"Extracting hero cards from image size: {width}x{height}")
            
            # Extract card 1 region
            card1_region = self.card_regions['hero_card1']
            x1 = int(width * card1_region['x_percent'])
            y1 = int(height * card1_region['y_percent'])
            w1 = int(width * card1_region['width_percent'])
            h1 = int(height * card1_region['height_percent'])
            
            # Ensure coordinates are within bounds
            x1 = max(0, min(x1, width - 1))
            y1 = max(0, min(y1, height - 1))
            w1 = max(1, min(w1, width - x1))
            h1 = max(1, min(h1, height - y1))
            
            card1_img = table_image[y1:y1+h1, x1:x1+w1].copy()
            
            # Extract card 2 region
            card2_region = self.card_regions['hero_card2']
            x2 = int(width * card2_region['x_percent'])
            y2 = int(height * card2_region['y_percent'])
            w2 = int(width * card2_region['width_percent'])
            h2 = int(height * card2_region['height_percent'])
            
            # Ensure coordinates are within bounds
            x2 = max(0, min(x2, width - 1))
            y2 = max(0, min(y2, height - 1))
            w2 = max(1, min(w2, width - x2))
            h2 = max(1, min(h2, height - y2))
            
            card2_img = table_image[y2:y2+h2, x2:x2+w2].copy()
            
            # Log extraction details
            self.logger.debug(f"Hero card 1 extracted: region ({x1},{y1},{w1},{h1}) -> image shape {card1_img.shape}")
            self.logger.debug(f"Hero card 2 extracted: region ({x2},{y2},{w2},{h2}) -> image shape {card2_img.shape}")
            
            # Save debug images with timestamp
            import time
            timestamp = int(time.time() * 1000)
            cv2.imwrite(f"debug_cards/hero_card1_extracted_{timestamp}.png", card1_img)
            cv2.imwrite(f"debug_cards/hero_card2_extracted_{timestamp}.png", card2_img)
            
            return card1_img, card2_img
            
        except Exception as e:
            self.logger.error(f"Error extracting card regions: {e}")
            import traceback
            traceback.print_exc()
            return np.array([]), np.array([])
    
    def preprocess_card_image(self, card_img: np.ndarray) -> Dict[str, np.ndarray]:
        """Enhanced preprocessing for better card recognition with multiple variants."""
        try:
            if card_img.size == 0:
                return {}
            
            processed = {}
            
            # Store original
            processed['original'] = card_img
            
            # Ensure we have a color image for color feature extraction
            if len(card_img.shape) == 3:
                color_img = card_img.copy()
                gray = cv2.cvtColor(card_img, cv2.COLOR_BGR2GRAY)
            else:
                # If grayscale input, try to create a color version for additional processing
                gray = card_img.copy()
                color_img = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            
            processed['grayscale'] = gray
            
            # Resize to standard size for consistent processing
            standard_height = 80
            aspect_ratio = gray.shape[1] / max(1, gray.shape[0])  # Avoid division by zero
            standard_width = int(standard_height * aspect_ratio)
            
            if standard_width < 1:
                standard_width = 1  # Ensure valid dimensions
            
            if gray.shape[0] != standard_height:
                gray = cv2.resize(gray, (standard_width, standard_height), interpolation=cv2.INTER_LINEAR)
                color_img = cv2.resize(color_img, (standard_width, standard_height), interpolation=cv2.INTER_LINEAR)
            
            # For card templates, focus on the upper portion where rank/suit are visible
            height = gray.shape[0]
            top_portion = gray[:int(height * 0.5), :]  # Use top 50% where rank/suit are located
            processed['top_focused'] = top_portion
            
            # Color analysis for suit detection (convert to HSV)
            hsv = cv2.cvtColor(color_img, cv2.COLOR_BGR2HSV)
            
            # Extract red regions (hearts/diamonds)
            lower_red1 = np.array([0, 100, 100])
            upper_red1 = np.array([10, 255, 255])
            red_mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
            
            lower_red2 = np.array([160, 100, 100])
            upper_red2 = np.array([180, 255, 255])
            red_mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
            
            red_mask = cv2.bitwise_or(red_mask1, red_mask2)
            processed['red_mask'] = red_mask
            
            # Extract black regions (clubs/spades)
            lower_black = np.array([0, 0, 0])
            upper_black = np.array([180, 255, 50])
            black_mask = cv2.inRange(hsv, lower_black, upper_black)
            processed['black_mask'] = black_mask
            
            # Apply denoising for cleaner processing
            denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
            processed['denoised'] = denoised
            
            # Enhanced contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(denoised)
            processed['enhanced'] = enhanced
            
            # Multiple thresholding methods for different lighting conditions
            # 1. OTSU threshold - good for bimodal images (black text on white)
            _, otsu_thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            processed['binary'] = otsu_thresh
            
            # 2. Adaptive threshold - handles varying lighting better
            adaptive_thresh = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                                   cv2.THRESH_BINARY, 11, 2)
            processed['adaptive'] = adaptive_thresh
            
            # Edge detection - focuses on card outlines and symbols
            edges = cv2.Canny(enhanced, 50, 150)
            processed['edges'] = edges
            
            # Morphological operations to clean up binary images
            kernel = np.ones((2,2), np.uint8)
            
            # Clean up OTSU result
            otsu_cleaned = cv2.morphologyEx(otsu_thresh, cv2.MORPH_CLOSE, kernel)
            otsu_cleaned = cv2.morphologyEx(otsu_cleaned, cv2.MORPH_OPEN, kernel)
            processed['binary_cleaned'] = otsu_cleaned
            
            # Apply same cleaning to adaptive threshold
            adaptive_cleaned = cv2.morphologyEx(adaptive_thresh, cv2.MORPH_CLOSE, kernel)
            processed['adaptive_cleaned'] = adaptive_cleaned
            
            # Feature enhancement - sharpen edges of ranks and suits
            kernel_sharpen = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            sharpened = cv2.filter2D(enhanced, -1, kernel_sharpen)
            processed['sharpened'] = sharpened
            
            # Extract corner - focus on top-left corner for rank/suit
            corner_size = min(int(gray.shape[0] * 0.3), int(gray.shape[1] * 0.3))
            if corner_size > 0:
                corner = gray[:corner_size, :corner_size]
                if corner.size > 0:
                    processed['corner'] = corner
                    
                    # Enhance corner contrast
                    corner_enhanced = clahe.apply(corner)
                    processed['corner_enhanced'] = corner_enhanced
            
            return processed
            
        except Exception as e:
            self.logger.error(f"Error preprocessing card image: {e}")
            return {}
            self.logger.error(f"Error preprocessing card image: {e}")
            return {}
    
    def recognize_card_by_template_matching(self, card_img: np.ndarray, debug=False) -> Optional[Card]:
        """Enhanced card recognition with multiple scale testing, color verification and confidence boosting."""
        try:
            if not self.template_loaded or card_img is None or card_img.size == 0:
                return None
            
            # Preprocess the card image with multiple variants
            processed = self.preprocess_card_image(card_img)
            if 'top_focused' not in processed:
                return None
            
            # Get multiple image variants for better matching
            image_variants = [
                (processed['top_focused'], "top_focused", 1.2),  # Primary target with boost
                (processed.get('enhanced', processed['top_focused']), "enhanced", 1.1),
                (processed.get('binary', processed['top_focused']), "binary", 0.9),
                (processed.get('adaptive', processed['top_focused']), "adaptive", 0.95),
                # Add edge detection variant
                (processed.get('edges', processed['top_focused']), "edges", 0.85),
                # Add corner focus for rank/suit detection
                (processed.get('corner_enhanced', processed['top_focused']), "corner", 1.3)
            ]
            
            best_match = None
            best_confidence = 0.0
            
            # Store debug results if requested
            if debug:
                self.debug_template_results = []
            
            # Try multiple scale factors for better matching across resolutions
            scale_factors = [0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15]
            
            # Try multiple template matching methods
            matching_methods = [
                (cv2.TM_CCOEFF_NORMED, 1.0, False),  # Normalized correlation
                (cv2.TM_CCORR_NORMED, 0.9, False),   # Normalized cross correlation
                (cv2.TM_SQDIFF_NORMED, 0.8, True)    # Squared difference (inverted)
            ]
            
            # Extract color information for suit verification
            is_red_suit = False
            is_black_suit = False
            if 'red_mask' in processed and 'black_mask' in processed:
                red_pixels = np.sum(processed['red_mask'] > 0)
                black_pixels = np.sum(processed['black_mask'] > 0)
                total_pixels = processed['red_mask'].size
                
                red_ratio = red_pixels / max(1, total_pixels)
                black_ratio = black_pixels / max(1, total_pixels)
                
                # Determine if card is more likely red or black suit
                is_red_suit = red_ratio > 0.05 and red_ratio > black_ratio
                is_black_suit = black_ratio > 0.05 and black_ratio > red_ratio
                
                self.logger.debug(f"Color analysis: red_ratio={red_ratio:.3f}, black_ratio={black_ratio:.3f}, "
                                f"is_red={is_red_suit}, is_black={is_black_suit}")
            
            # Save original image with timestamp for debugging
            timestamp = int(time.time() * 1000)
            debug_filename = f"debug_cards/card_recognition_{timestamp}.png"
            cv2.imwrite(debug_filename, card_img)
            
            # Track all potential matches for weighted consensus
            all_matches = {}
            
            for card_name, template in self.card_templates.items():
                # Skip if template doesn't exist
                if template is None or template.size == 0:
                    continue
                    
                # Apply color verification to filter out wrong suit colors early
                card_suit = card_name[1]  # Extract suit character
                suit_color_valid = True
                
                # Skip red templates for likely black cards and vice versa
                if is_red_suit and card_suit in ['c', 's']:  # Clubs and Spades are black
                    suit_color_valid = False
                elif is_black_suit and card_suit in ['h', 'd']:  # Hearts and Diamonds are red
                    suit_color_valid = False
                
                # Skip invalid color matches unless confidence is very high
                if not suit_color_valid:
                    continue
                
                # Initialize score for this card
                card_score = 0
                match_count = 0
                
                for img_variant, variant_name, confidence_multiplier in image_variants:
                    if img_variant is None:
                        continue
                    
                    for scale_factor in scale_factors:
                        # Scale the image variant
                        if scale_factor != 1.0:
                            h, w = img_variant.shape[:2]
                            scaled_img = cv2.resize(img_variant, 
                                                  (int(w * scale_factor), int(h * scale_factor)),
                                                  interpolation=cv2.INTER_LINEAR)
                        else:
                            scaled_img = img_variant
                    
                        for method, method_weight, invert_score in matching_methods:
                            try:
                                # Resize template to match target if needed
                                if template.shape[0] != scaled_img.shape[0] or template.shape[1] != scaled_img.shape[1]:
                                    template_resized = cv2.resize(template, 
                                                               (scaled_img.shape[1], scaled_img.shape[0]),
                                                               interpolation=cv2.INTER_LINEAR)
                                else:
                                    template_resized = template
                                
                                # Apply additional preprocessing to template if needed
                                if variant_name in ['binary', 'adaptive', 'edges'] and len(template_resized.shape) == 3:
                                    template_resized = cv2.cvtColor(template_resized, cv2.COLOR_BGR2GRAY)
                                
                                # Perform template matching
                                result = cv2.matchTemplate(scaled_img, template_resized, method)
                                _, max_val, _, _ = cv2.minMaxLoc(result)
                                
                                # Handle inverted scores for SQDIFF
                                if invert_score:
                                    max_val = 1.0 - max_val
                                
                                # Apply weights, multipliers and scale boost
                                # Scale factor close to 1.0 gets a boost
                                scale_boost = 1.0 - abs(scale_factor - 1.0) * 0.5
                                final_score = max_val * confidence_multiplier * method_weight * scale_boost
                                
                                # Apply additional suit color verification boost/penalty
                                if suit_color_valid:
                                    final_score *= 1.2  # Boost score for color-matched suits
                                else:
                                    final_score *= 0.5  # Severely penalize wrong suit colors
                                
                                # Only consider reasonable matches
                                if final_score > 0.6:
                                    card_score += final_score
                                    match_count += 1
                                    
                                    # Track best overall match
                                    if final_score > best_confidence:
                                        best_confidence = final_score
                                        best_match = Card(
                                            rank=card_name[0],
                                            suit=card_name[1],
                                            confidence=final_score
                                        )
                                        
                                        # Log successful matches for debugging
                                        self.logger.debug(f"New best match: {card_name} via {variant_name}+{method}+{scale_factor} = {final_score:.3f}")
                                        
                                        # Save debug comparison
                                        if debug:
                                            self._save_debug_comparison(scaled_img, template_resized, 
                                                                      card_name, final_score, 
                                                                      f"{variant_name}_{method}_{scale_factor}")
                            
                            except Exception as e:
                                self.logger.debug(f"Error matching {card_name} with {variant_name}: {e}")
                                continue
                
                # Calculate average score for this card across all variants/methods/scales
                if match_count > 0:
                    avg_score = card_score / match_count
                    all_matches[card_name] = (avg_score, match_count)
                    
                    # Store for debug output
                    if debug and template is not None:
                        self.debug_template_results.append((card_name, avg_score, template))
            
            # If we have debug information, sort by score
            if debug and hasattr(self, 'debug_template_results'):
                self.debug_template_results.sort(key=lambda x: x[1], reverse=True)
            
            # Validate best match using consensus if we have multiple good matches
            if len(all_matches) > 1:
                # Check if there's a clear consensus on rank
                rank_scores = {}
                for card_name, (score, count) in all_matches.items():
                    rank = card_name[0]
                    if rank not in rank_scores:
                        rank_scores[rank] = (0, 0)
                    
                    current_score, current_count = rank_scores[rank]
                    rank_scores[rank] = (current_score + score, current_count + count)
                
                # Find best rank by total score
                best_rank = None
                best_rank_score = 0
                for rank, (total_score, count) in rank_scores.items():
                    avg_score = total_score / max(1, count)
                    if avg_score > best_rank_score:
                        best_rank_score = avg_score
                        best_rank = rank
                
                # If best match rank doesn't match consensus rank, and consensus is strong, override
                if (best_match and best_match.rank != best_rank and 
                    best_rank_score > best_confidence * 1.1):  # 10% better consensus
                    
                    # Find best match with consensus rank
                    for card_name, (score, _) in all_matches.items():
                        if card_name[0] == best_rank and score > best_confidence * 0.9:  # Within 10% of best
                            best_match = Card(
                                rank=card_name[0],
                                suit=card_name[1],
                                confidence=score
                            )
                            best_confidence = score
                            self.logger.debug(f"Override to consensus rank {best_rank}: {card_name} with score {score:.3f}")
                            break
            
            if best_match and best_confidence > 0.6:  # Lower threshold from 0.7 to 0.6
                self.logger.debug(f"Final template match: {best_match.rank}{best_match.suit} (confidence: {best_confidence:.3f})")
                return best_match
            else:
                self.logger.debug(f"No confident template match found. Best score: {best_confidence:.3f}")
                return None
            
        except Exception as e:
            self.logger.error(f"Error in enhanced template matching: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def recognize_card_by_ocr(self, card_img: np.ndarray) -> Optional[Card]:
        """Recognize card using OCR as fallback method."""
        try:
            if card_img.size == 0:
                return None
            
            # Preprocess for OCR
            processed = self.preprocess_card_image(card_img)
            if 'binary' not in processed:
                return None
            
            # Use OCR to extract text
            ocr_img = processed['binary']
            
            # Configure OCR for single characters
            custom_config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=23456789TJQKA♠♥♦♣hdcs'
            
            try:
                if not PYTESSERACT_AVAILABLE:
                    return None
                    
                text = pytesseract.image_to_string(ocr_img, config=custom_config).strip()
                
                if len(text) >= 2:
                    # Parse rank and suit
                    rank_char = text[0].upper()
                    suit_char = text[1].lower()
                    
                    # Map characters to standard format
                    rank_map = {'1': 'T', '0': 'T'}  # Common OCR mistakes
                    suit_map = {'♠': 's', '♥': 'h', '♦': 'd', '♣': 'c'}
                    
                    rank = rank_map.get(rank_char, rank_char)
                    suit = suit_map.get(suit_char, suit_char)
                    
                    # Validate rank and suit
                    valid_ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
                    valid_suits = ['h', 'd', 'c', 's']
                    
                    if rank in valid_ranks and suit in valid_suits:
                        return Card(rank=rank, suit=suit, confidence=0.5)  # Lower confidence for OCR
                        
            except Exception as ocr_error:
                self.logger.debug(f"OCR failed: {ocr_error}")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in OCR recognition: {e}")
            return None
    
    def recognize_single_card(self, card_img: np.ndarray, card_name=None, debug=False) -> Optional[Card]:
        """
        Recognize a single card and return a Card object.
        This is a bridge method to standardize the API for different detector components.
        
        Args:
            card_img: Image of the card to recognize
            card_name: Optional name identifier for the card (useful for debugging)
            debug: Whether to collect debug information
            
        Returns:
            Card object with rank, suit and confidence if detected, None otherwise
        """
        if debug and card_name:
            self.logger.info(f"Recognizing card: {card_name}")
            
        card_str, confidence, method = self.recognize_card(card_img, debug=debug)
        
        if not card_str or card_str == "Unknown":
            return None
            
        # Parse the card string (format: '2h', 'Kd', etc.)
        if len(card_str) >= 2:
            rank = card_str[0].upper()
            suit = card_str[1].lower()
            return Card(rank=rank, suit=suit, confidence=confidence)
        
        return None
    
    def recognize_card(self, card_img: np.ndarray, debug=False) -> Tuple[str, float, str]:
        """
        Main card recognition function combining multiple methods.
        
        Args:
            card_img: The card image to recognize
            debug: Whether to save debug information
            
        Returns:
            Tuple of (card_name, confidence, method_used)
        """
        try:
            # Save original image for debugging
            if debug:
                timestamp = int(time.time() * 1000)
                debug_file = f"debug_cards/input_card_{timestamp}.png"
                cv2.imwrite(debug_file, card_img)
            
            # First try template matching (most reliable)
            template_match = self.recognize_card_by_template_matching(card_img, debug=debug)
            if template_match and template_match.confidence > 0.6:
                card_name = f"{template_match.rank}{template_match.suit}"
                return card_name, template_match.confidence, "template"
            
            # Fallback to OCR
            ocr_match = self.recognize_card_by_ocr(card_img)
            if ocr_match and ocr_match.confidence > 0.6:
                card_name = f"{ocr_match.rank}{ocr_match.suit}"
                return card_name, ocr_match.confidence, "ocr"
            
            # If we got a weak template match, use that as last resort
            if template_match:
                card_name = f"{template_match.rank}{template_match.suit}"
                return card_name, template_match.confidence, "weak_template"
            
            # If we got a weak OCR match, use that as last resort
            if ocr_match:
                card_name = f"{ocr_match.rank}{ocr_match.suit}"
                return card_name, ocr_match.confidence, "weak_ocr"
            
            # No successful match
            return "unknown", 0.0, "none"
            
        except Exception as e:
            self.logger.error(f"Error in card recognition: {e}")
            return "error", 0.0, "error"
            
        except Exception as e:
            self.logger.error(f"Error recognizing card: {e}")
            return None
    
    def recognize_hero_hole_cards(self, table_image: np.ndarray, debug=False) -> HoleCards:
        """Recognize the hero's hole cards from the table image."""
        try:
            timestamp = time.time()
            
            if debug:
                self.logger.info("Starting hero card recognition with debug mode enabled")
            
            # Extract card regions
            card1_img, card2_img = self.extract_hero_cards_region(table_image)
            
            if card1_img.size == 0 or card2_img.size == 0:
                self.logger.warning("Could not extract card regions")
                return HoleCards(timestamp=timestamp)
            
            if debug and card1_img.size > 0 and card2_img.size > 0:
                self.logger.info(f"Successfully extracted hero card regions: {card1_img.shape}, {card2_img.shape}")
            
            # Recognize each card
            card1 = self.recognize_single_card(card1_img, card_name="hero_card1", debug=debug)
            card2 = self.recognize_single_card(card2_img, card_name="hero_card2", debug=debug)
            
            # Calculate overall confidence
            confidence = 0.0
            if card1 and card2:
                confidence = (card1.confidence + card2.confidence) / 2
            elif card1 or card2:
                confidence = (card1.confidence if card1 else card2.confidence) / 2
            
            hole_cards = HoleCards(
                card1=card1,
                card2=card2,
                detection_confidence=confidence,
                timestamp=timestamp
            )
            
            # Log results
            if hole_cards.is_valid():
                self.logger.info(f"Hole Cards Detected: {hole_cards} (confidence: {confidence:.3f})")
            else:
                self.logger.debug(f"Hole cards detection incomplete: Card1={card1}, Card2={card2}")
            
            return hole_cards
            
        except Exception as e:
            self.logger.error(f"Error recognizing hole cards: {e}")
            return HoleCards(timestamp=time.time())
    
    def save_card_for_template(self, card_img: np.ndarray, suggested_name: str = None):
        """Save a card image for manual template creation."""
        try:
            timestamp = int(time.time())
            if suggested_name:
                filename = f"card_templates/manual_{suggested_name}_{timestamp}.png"
            else:
                filename = f"card_templates/manual_card_{timestamp}.png"
            
            cv2.imwrite(filename, card_img)
            self.logger.info(f"Saved card image for template creation: {filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving card template: {e}")
    
    def get_recognition_stats(self) -> Dict[str, Any]:
        """Get statistics about card recognition performance."""
        return {
            'templates_loaded': len(self.card_templates),
            'template_matching_enabled': self.template_loaded,
            'template_threshold': self.template_match_threshold,
            'ocr_threshold': self.ocr_confidence_threshold,
            'card_regions_defined': len(self.card_regions)
        }
    
    def _save_debug_comparison(self, card_img: np.ndarray, template_img: np.ndarray, 
                              match_name: str, score: float, region_name: str = "unknown"):
        """Save a debug image showing the card and its matched template."""
        try:
            import os
            import time
            
            # Ensure debug directory exists
            os.makedirs("debug_cards", exist_ok=True)
            
            # Resize images to same size for comparison
            height = max(card_img.shape[0], template_img.shape[0])
            width = max(card_img.shape[1], template_img.shape[1])
            
            # Resize both images
            card_resized = cv2.resize(card_img, (width, height))
            template_resized = cv2.resize(template_img, (width, height))
            
            # Create a comparison image (side by side + difference)
            comparison = np.zeros((height, width * 3 + 20, 3), dtype=np.uint8)
            
            # Add the extracted card
            if len(card_resized.shape) == 3:
                comparison[0:height, 0:width] = card_resized
            else:
                comparison[0:height, 0:width] = cv2.cvtColor(card_resized, cv2.COLOR_GRAY2BGR)
            
            # Add separator
            comparison[:, width:width+10] = [255, 255, 255]
            
            # Add the matched template
            if len(template_resized.shape) == 3:
                comparison[0:height, width+10:width*2+10] = template_resized
            else:
                comparison[0:height, width+10:width*2+10] = cv2.cvtColor(template_resized, cv2.COLOR_GRAY2BGR)
            
            # Add separator
            comparison[:, width*2+10:width*2+20] = [255, 255, 255]
            
            # Add difference image
            if len(card_resized.shape) != len(template_resized.shape):
                if len(card_resized.shape) == 3:
                    card_gray = cv2.cvtColor(card_resized, cv2.COLOR_BGR2GRAY)
                else:
                    card_gray = card_resized
                if len(template_resized.shape) == 3:
                    template_gray = cv2.cvtColor(template_resized, cv2.COLOR_BGR2GRAY)
                else:
                    template_gray = template_resized
                diff = cv2.absdiff(card_gray, template_gray)
                diff_bgr = cv2.cvtColor(diff, cv2.COLOR_GRAY2BGR)
            else:
                diff = cv2.absdiff(card_resized, template_resized)
                if len(diff.shape) == 2:
                    diff_bgr = cv2.cvtColor(diff, cv2.COLOR_GRAY2BGR)
                else:
                    diff_bgr = diff
            
            comparison[0:height, width*2+20:] = diff_bgr
            
            # Add text labels
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            thickness = 1
            color = (0, 255, 0)  # Green text
            
            cv2.putText(comparison, f"Extracted ({region_name})", (5, height-10), 
                       font, font_scale, color, thickness)
            cv2.putText(comparison, f"Template: {match_name}", (width+15, height-10), 
                       font, font_scale, color, thickness)
            cv2.putText(comparison, f"Score: {score:.3f}", (width*2+25, height-30), 
                       font, font_scale, color, thickness)
            cv2.putText(comparison, "Difference", (width*2+25, height-10), 
                       font, font_scale, color, thickness)
            
            # Save the comparison
            timestamp = int(time.time() * 1000)
            filename = f"debug_cards/comparison_{region_name}_{match_name}_{timestamp}.png"
            cv2.imwrite(filename, comparison)
            self.logger.debug(f"Saved debug comparison: {filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving debug comparison: {e}")
    
    def test_region_extraction(self, table_image: np.ndarray):
        """Test method to verify region extraction is working correctly."""
        try:
            self.logger.info("=== Testing Hero Card Region Extraction ===")
            height, width = table_image.shape[:2]
            self.logger.info(f"Table image size: {width}x{height}")
            
            for region_name, region_data in self.card_regions.items():
                self.logger.info(f"\nTesting region: {region_name}")
                self.logger.info(f"Region percentages: x={region_data['x_percent']:.4f}, "
                               f"y={region_data['y_percent']:.4f}, "
                               f"w={region_data['width_percent']:.4f}, "
                               f"h={region_data['height_percent']:.4f}")
                
                # Calculate pixel coordinates
                x = int(width * region_data['x_percent'])
                y = int(height * region_data['y_percent'])
                w = int(width * region_data['width_percent'])
                h = int(height * region_data['height_percent'])
                
                self.logger.info(f"Pixel coordinates: x={x}, y={y}, w={w}, h={h}")
                
                # Extract region
                extracted = table_image[y:y+h, x:x+w].copy()
                self.logger.info(f"Extracted image shape: {extracted.shape}")
                
                # Save for inspection
                import time
                timestamp = int(time.time() * 1000)
                filename = f"debug_cards/region_test_{region_name}_{timestamp}.png"
                cv2.imwrite(filename, extracted)
                self.logger.info(f"Saved test extraction: {filename}")
                
        except Exception as e:
            self.logger.error(f"Error testing region extraction: {e}")
            import traceback
            traceback.print_exc()