"""
Test the modified capture loop functionality with existing debug images.
This script simulates the behavior of the capture loop without relying on live capture.
"""

import os
import cv2
import time
import logging
import sys

# Add src directory to the path to find modules
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

# Import the PokerStarsBot
from src.poker_bot import PokerStarsBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_capture_loop')

class CaptureLoopTester:
    def __init__(self):
        self.bot = None
        self.capture_count = 0
        self.success_count = 0
        
    def log_message(self, message):
        """Simulate log message function."""
        logger.info(message)
        
    def initialize_bot(self):
        """Initialize the bot components."""
        try:
            self.bot = PokerStarsBot()
            self.log_message("✅ Bot initialized successfully")
        except Exception as e:
            self.log_message(f"❌ Bot initialization failed: {e}")
            import traceback
            self.log_message(f"Traceback: {traceback.format_exc()}")
    
    def has_valid_detection(self, analysis):
        """Check if analysis contains valid detections."""
        if not analysis:
            return False
        
        # Check for any valid detections
        valid_detections = 0
        
        # Check hole cards
        if 'hole_cards' in analysis and analysis['hole_cards']:
            hole_cards = analysis['hole_cards']
            if hasattr(hole_cards, 'is_valid') and hole_cards.is_valid():
                valid_detections += 1
        
        # Check community cards
        if 'community_cards' in analysis and analysis['community_cards']:
            community_cards = analysis['community_cards']
            if hasattr(community_cards, 'count') and community_cards.count > 0:
                valid_detections += 1
        
        # Check table info
        if 'table_info' in analysis and analysis['table_info']:
            table_info = analysis['table_info']
            if hasattr(table_info, 'players') and len(table_info.players) > 0:
                valid_detections += 1
        
        return valid_detections > 0
    
    def test_with_image(self, image_path):
        """Test the analysis process with a single image."""
        self.log_message(f"📊 Testing with image: {os.path.basename(image_path)}")
        
        # Read image
        screenshot = cv2.imread(image_path)
        if screenshot is None or screenshot.size == 0:
            self.log_message("❌ Failed to read image")
            return
        
        # Ensure bot is initialized
        if not self.bot:
            self.initialize_bot()
        
        # Start time
        start_time = time.time()
        
        # Log that analysis is starting
        self.log_message(f"🔍 Starting analysis of frame #{self.capture_count+1}...")
        
        # Run analysis with debug mode
        debug_mode = True  # Enable debug for all test images
        
        try:
            # Perform the analysis
            analysis = self.bot.analyze_game_state(screenshot, debug=debug_mode)
            
            # Validate analysis results
            if analysis and isinstance(analysis, dict):
                # Log successful analysis with detected cards
                card_info = ""
                if 'hole_cards' in analysis and analysis['hole_cards'] and hasattr(analysis['hole_cards'], 'is_valid'):
                    if analysis['hole_cards'].is_valid():
                        card_info = f"Hole cards: {analysis['hole_cards']}"
                
                if 'community_cards' in analysis and analysis['community_cards'] and hasattr(analysis['community_cards'], 'cards'):
                    comm_cards = [str(c) for c in analysis['community_cards'].cards if c]
                    if comm_cards:
                        card_info += f", Community: {', '.join(comm_cards)}"
                
                # Log analysis completion with detailed results
                if card_info:
                    self.log_message(f"✅ Analysis complete: {card_info}")
                else:
                    self.log_message("⚠️ Analysis complete, but no cards detected")
                
                # Update statistics
                self.capture_count += 1
                if self.has_valid_detection(analysis):
                    self.success_count += 1
                    self.log_message(f"🎯 Detection successful: {self.success_count}/{self.capture_count}")
                
                # Show elapsed time
                elapsed = time.time() - start_time
                self.log_message(f"⏱️ Analysis took {elapsed:.2f} seconds")
                
                # Simulate waiting period between captures
                min_capture_interval = 2.0
                remaining_interval = max(0.5, min_capture_interval - elapsed)
                self.log_message(f"⏱️ Waiting {remaining_interval:.1f} seconds before next capture...")
                
                # Reduced wait time for testing
                time.sleep(0.5)
                
            else:
                self.log_message("⚠️ Analysis returned invalid results")
                
        except Exception as analysis_error:
            self.log_message(f"⚠️ Analysis error: {analysis_error}")
            import traceback
            self.log_message(f"Traceback: {traceback.format_exc()}")
    
    def run_tests(self, image_directory, limit=5):
        """Run tests on all images in the directory, up to the specified limit."""
        self.log_message(f"🏁 Starting test run with images from {image_directory}")
        
        # Get all analysis images
        image_files = [f for f in os.listdir(image_directory) if f.startswith('analysis_') and f.endswith('.png')]
        
        # Limit the number of images to process
        if limit and len(image_files) > limit:
            image_files = image_files[:limit]
            self.log_message(f"ℹ️ Limited to {limit} images for testing")
        
        # Process each image
        for image_file in image_files:
            image_path = os.path.join(image_directory, image_file)
            self.test_with_image(image_path)
            self.log_message("-" * 40)  # Separator between tests
        
        # Show summary
        self.log_message(f"📋 Test Summary: {self.success_count}/{self.capture_count} successful detections")

def main():
    # Create tester
    tester = CaptureLoopTester()
    
    # Run tests with debug images
    debug_dir = "debug_images"
    tester.run_tests(debug_dir, limit=3)  # Process 3 images for testing

if __name__ == "__main__":
    main()
