#!/usr/bin/env python3
"""
Comprehensive test to verify the region loading integration.
This will test every step of the region loading and recognition pipeline.
"""

import sys
import json
import cv2
import numpy as np
import logging
import time
sys.path.append('src')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(name)s - %(message)s')

def main():
    print("=" * 60)
    print("COMPREHENSIVE REGION INTEGRATION TEST")
    print("=" * 60)
    
    # Test 1: Check region config file
    print("\n1. CHECKING REGION CONFIG FILE")
    print("-" * 40)
    try:
        with open('regions/region_config.json', 'r') as f:
            config = json.load(f)
        
        print(f"✅ Config file exists")
        print(f"   Version: {config.get('version', 'unknown')}")
        print(f"   Timestamp: {config.get('timestamp', 'unknown')}")
        print(f"   Image dimensions: {config.get('image_dimensions', 'unknown')}")
        print(f"   Regions found: {len(config.get('regions', {}))}")
        
        for name, region in config.get('regions', {}).items():
            print(f"   {name}: x={region['x']:.2f}%, y={region['y']:.2f}%, "
                  f"w={region['width']:.2f}%, h={region['height']:.2f}%")
    except Exception as e:
        print(f"❌ Error reading config: {e}")
        return
    
    # Test 2: RegionLoader functionality
    print("\n2. TESTING REGIONLOADER")
    print("-" * 40)
    try:
        from region_loader import RegionLoader
        loader = RegionLoader()
        
        # Test basic loading
        regions = loader.load_regions()
        print(f"✅ RegionLoader loaded {len(regions)} regions")
        
        # Test community card regions
        community_regions = loader.get_community_card_regions()
        print(f"✅ Community card regions: {len(community_regions)}")
        for name, region in community_regions.items():
            print(f"   {name}: x={region['x_percent']:.4f}, y={region['y_percent']:.4f}")
        
        # Test hero card regions
        hero_regions = loader.get_hero_card_regions()
        print(f"✅ Hero card regions: {len(hero_regions)}")
        for name, region in hero_regions.items():
            print(f"   {name}: x={region['x_percent']:.4f}, y={region['y_percent']:.4f}")
        
    except Exception as e:
        print(f"❌ RegionLoader error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 3: CardRecognizer initialization
    print("\n3. TESTING CARDRECOGNIZER INITIALIZATION")
    print("-" * 40)
    try:
        from card_recognizer import CardRecognizer
        recognizer = CardRecognizer()
        
        print(f"✅ CardRecognizer created")
        print(f"   Regions loaded: {len(recognizer.card_regions)}")
        print(f"   Templates loaded: {len(recognizer.card_templates)}")
        
        for name, region in recognizer.card_regions.items():
            print(f"   {name}: x={region['x_percent']:.4f}, y={region['y_percent']:.4f}, "
                  f"w={region['width_percent']:.4f}, h={region['height_percent']:.4f}")
        
    except Exception as e:
        print(f"❌ CardRecognizer error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 4: CommunityCardDetector initialization
    print("\n4. TESTING COMMUNITYCARDDETECTOR INITIALIZATION")
    print("-" * 40)
    try:
        from community_card_detector import CommunityCardDetector
        detector = CommunityCardDetector(recognizer)
        
        print(f"✅ CommunityCardDetector created")
        print(f"   Regions loaded: {len(detector.community_card_regions)}")
        
        for name, region in detector.community_card_regions.items():
            print(f"   {name}: x={region['x_percent']:.4f}, y={region['y_percent']:.4f}, "
                  f"w={region['width_percent']:.4f}, h={region['height_percent']:.4f}")
        
    except Exception as e:
        print(f"❌ CommunityCardDetector error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 5: Bot initialization
    print("\n5. TESTING BOT INITIALIZATION")
    print("-" * 40)
    try:
        from poker_bot import PokerStarsBot
        bot = PokerStarsBot()
        
        print(f"✅ PokerStarsBot created")
        print(f"   CardRecognizer regions: {len(bot.card_recognizer.card_regions)}")
        print(f"   CommunityCardDetector regions: {len(bot.community_detector.community_card_regions)}")
        
        # Verify regions are the saved ones, not defaults
        hero_region = bot.card_recognizer.card_regions.get('hero_card1', {})
        community_region = bot.community_detector.community_card_regions.get('card_1', {})
        
        print(f"   Hero card 1 region: x={hero_region.get('x_percent', 0):.4f}")
        print(f"   Community card 1 region: x={community_region.get('x_percent', 0):.4f}")
        
        # Check if these match our config (should be around 0.434 and 0.333)
        expected_hero_x = 43.400707104298384 / 100.0  # From config
        expected_community_x = 33.274927460304596 / 100.0  # From config
        
        hero_match = abs(hero_region.get('x_percent', 0) - expected_hero_x) < 0.001
        community_match = abs(community_region.get('x_percent', 0) - expected_community_x) < 0.001
        
        if hero_match and community_match:
            print("✅ Bot is using SAVED regions (not defaults)")
        else:
            print("❌ Bot is using DEFAULT regions (not saved)")
            print(f"   Expected hero x: {expected_hero_x:.4f}, got: {hero_region.get('x_percent', 0):.4f}")
            print(f"   Expected community x: {expected_community_x:.4f}, got: {community_region.get('x_percent', 0):.4f}")
        
    except Exception as e:
        print(f"❌ Bot initialization error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 6: Test with actual screenshot if available
    print("\n6. TESTING WITH SCREENSHOT")
    print("-" * 40)
    
    # Look for recent screenshots
    import glob
    import os
    
    screenshot_paths = []
    for pattern in ["screenshots/*.png", "debug_images/*.png", "*.png"]:
        screenshot_paths.extend(glob.glob(pattern))
    
    # Sort by modification time, get most recent
    if screenshot_paths:
        screenshot_paths.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        screenshot_path = screenshot_paths[0]
        
        try:
            screenshot = cv2.imread(screenshot_path)
            if screenshot is not None:
                print(f"✅ Loaded screenshot: {screenshot_path}")
                print(f"   Image dimensions: {screenshot.shape[1]}x{screenshot.shape[0]}")
                
                # Test region extraction
                recognizer.test_region_extraction(screenshot)
                
                # Test hero card recognition
                print("   Testing hero card recognition...")
                hero_cards = recognizer.recognize_hero_hole_cards(screenshot)
                print(f"   Hero cards result: {hero_cards}")
                
                # Test community card detection
                print("   Testing community card detection...")
                community_cards = detector.detect_community_cards(screenshot)
                print(f"   Community cards result: {community_cards}")
                
            else:
                print(f"❌ Could not load screenshot: {screenshot_path}")
        except Exception as e:
            print(f"❌ Screenshot test error: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("⚠️ No screenshots found for testing")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
