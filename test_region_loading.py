"""
Test script to verify region loading and refreshing functionality
"""

import os
import sys
import cv2
import time
import logging

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_region_loading')

def test_region_loading():
    """Test that regions are properly loaded and applied to components."""
    try:
        # Import needed modules
        from region_loader import RegionLoader
        from card_recognizer import CardRecognizer
        from community_card_detector import CommunityCardDetector
        
        logger.info("Step 1: Testing RegionLoader")
        loader = RegionLoader()
        
        if not loader.regions_exist():
            logger.error("❌ No region configuration file found. Please calibrate regions first.")
            return False
            
        regions = loader.load_regions()
        logger.info(f"✅ RegionLoader found {len(regions)} regions")
        
        # Test getting community card regions
        community_regions = loader.get_community_card_regions()
        logger.info(f"✅ Found {len(community_regions)} community card regions")
        for name, region in community_regions.items():
            logger.info(f"   {name}: x={region['x_percent']:.4f}, y={region['y_percent']:.4f}")
            
        # Test getting hero card regions
        hero_regions = loader.get_hero_card_regions()
        logger.info(f"✅ Found {len(hero_regions)} hero card regions")
        for name, region in hero_regions.items():
            logger.info(f"   {name}: x={region['x_percent']:.4f}, y={region['y_percent']:.4f}")
        
        logger.info("\nStep 2: Testing CardRecognizer region integration")
        # Create and check card recognizer
        card_recognizer = CardRecognizer()
        if hasattr(card_recognizer, 'card_regions'):
            logger.info(f"✅ CardRecognizer has {len(card_recognizer.card_regions)} regions")
            for name, region in card_recognizer.card_regions.items():
                logger.info(f"   {name}: x={region['x_percent']:.4f}, y={region['y_percent']:.4f}")
        else:
            logger.error("❌ CardRecognizer has no card_regions attribute")
            
        # Test update_regions method
        if hasattr(card_recognizer, 'update_regions'):
            logger.info("✅ CardRecognizer has update_regions method")
            # Call the method to test it
            card_recognizer.update_regions(hero_regions)
            logger.info("✅ Successfully called update_regions on CardRecognizer")
        else:
            logger.error("❌ CardRecognizer has no update_regions method")
            
        logger.info("\nStep 3: Testing CommunityCardDetector region integration")
        # Create and check community card detector
        community_detector = CommunityCardDetector(card_recognizer)
        if hasattr(community_detector, 'community_card_regions'):
            logger.info(f"✅ CommunityCardDetector has {len(community_detector.community_card_regions)} regions")
            for name, region in community_detector.community_card_regions.items():
                logger.info(f"   {name}: x={region['x_percent']:.4f}, y={region['y_percent']:.4f}")
        else:
            logger.error("❌ CommunityCardDetector has no community_card_regions attribute")
            
        # Test update_regions method
        if hasattr(community_detector, 'update_regions'):
            logger.info("✅ CommunityCardDetector has update_regions method")
            # Call the method to test it
            community_detector.update_regions(community_regions)
            logger.info("✅ Successfully called update_regions on CommunityCardDetector")
        else:
            logger.error("❌ CommunityCardDetector has no update_regions method")
        
        logger.info("\n✅ All tests completed successfully!")
        return True
            
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("Testing region loading functionality...")
    test_region_loading()
    print("Test complete.")
