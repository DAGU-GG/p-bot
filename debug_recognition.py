#!/usr/bin/env python3
"""
Debug script to visualize card recognition process and check extraction vs recognition
"""

import cv2
import numpy as np
import os
import sys
import json
from datetime import datetime
import time

# Add src to path
sys.path.append('src')

def test_recognition():
    """Test card recognition on the latest screenshot."""
    
    print("=== Card Recognition Debug ===")
    
    # Check if we have a recent screenshot
    screenshots = []
    if os.path.exists('screenshots'):
        screenshots = [f for f in os.listdir('screenshots') if f.endswith('.png')]
        screenshots.sort(key=lambda x: os.path.getmtime(f'screenshots/{x}'), reverse=True)
    
    if not screenshots:
        print("❌ No screenshots found in screenshots/ folder")
        return
    
    latest_screenshot = f'screenshots/{screenshots[0]}'
    print(f"📸 Using latest screenshot: {latest_screenshot}")
    
    # Import needed components
    from card_recognizer import CardRecognizer
    from community_card_detector import CommunityCardDetector
    
    # Initialize the components
    card_recognizer = CardRecognizer()
    community_detector = CommunityCardDetector(card_recognizer)
    
    # Load the screenshot
    image = cv2.imread(latest_screenshot)
    if image is None:
        print("❌ Could not load screenshot")
        return
    
    height, width = image.shape[:2]
    print(f"📐 Image dimensions: {width}x{height}")
    
    print("\n=== Testing Community Card Extraction and Recognition ===")
    
    # Create folders for debug outputs
    os.makedirs("debug_extracted", exist_ok=True)
    os.makedirs("debug_matched", exist_ok=True)
    
    # Extract and recognize each community card
    timestamp = int(time.time())
    for i in range(1, 6):
        card_key = f'card_{i}'
        if card_key in community_detector.community_card_regions:
            region = community_detector.community_card_regions[card_key]
            print(f"\nCommunity Card {i}:")
            print(f"  Region settings: x={region['x_percent']:.4f}, y={region['y_percent']:.4f}, w={region['width_percent']:.4f}, h={region['height_percent']:.4f}")
            
            # Calculate pixel coordinates
            x = int(width * region['x_percent'])
            y = int(height * region['y_percent'])
            w = int(width * region['width_percent'])
            h = int(height * region['height_percent'])
            print(f"  Pixel coords: ({x}, {y}, {w}, {h})")
            
            # Extract region
            if y+h <= height and x+w <= width and x >= 0 and y >= 0:
                card_img = image[y:y+h, x:x+w].copy()
                
                # Save extracted image
                extract_file = f"debug_extracted/comm_card_{i}_{timestamp}.png"
                cv2.imwrite(extract_file, card_img)
                print(f"  ✅ Extracted image saved to: {extract_file}")
                
                # Check if card present
                is_present = community_detector._is_card_present(card_img)
                print(f"  Card present: {is_present}")
                
                if is_present:
                    # Try template matching
                    card = card_recognizer.recognize_card_by_template_matching(card_img)
                    if card:
                        print(f"  ✅ Template match: {card} (confidence: {card.confidence:.3f})")
                        
                        # Save the template that matched
                        template_key = f"{card.rank}{card.suit}"
                        if template_key in card_recognizer.card_templates:
                            template = card_recognizer.card_templates[template_key]
                            template_file = f"debug_matched/template_{template_key}_{timestamp}.png"
                            cv2.imwrite(template_file, template)
                            print(f"  ✅ Matched template saved to: {template_file}")
                            
                            # Create side-by-side comparison
                            card_resized = cv2.resize(card_img, (100, 140))
                            template_resized = cv2.resize(template, (100, 140))
                            
                            # Create comparison image
                            comparison = np.zeros((140, 210, 3), dtype=np.uint8)
                            if len(card_resized.shape) == 2:
                                card_resized = cv2.cvtColor(card_resized, cv2.COLOR_GRAY2BGR)
                            comparison[:, :100] = card_resized
                            
                            # Add separator line
                            comparison[:, 100:110] = [255, 255, 255]
                            
                            if len(template_resized.shape) == 2:
                                template_resized = cv2.cvtColor(template_resized, cv2.COLOR_GRAY2BGR)
                            comparison[:, 110:] = template_resized
                            
                            compare_file = f"debug_matched/compare_{card_key}_{template_key}_{timestamp}.png"
                            cv2.imwrite(compare_file, comparison)
                            print(f"  ✅ Comparison image saved to: {compare_file}")
                    else:
                        # Try OCR
                        ocr_card = card_recognizer.recognize_card_by_ocr(card_img)
                        if ocr_card:
                            print(f"  ⚠️ OCR fallback match: {ocr_card}")
                        else:
                            print(f"  ❌ No card recognized")
                else:
                    print(f"  ⚠️ No card detected in region")
            else:
                print(f"  ❌ Region coordinates out of bounds")
    
    print("\n=== Testing Hero Card Extraction and Recognition ===")
    
    # Extract and recognize hero cards
    card1_img, card2_img = card_recognizer.extract_hero_cards_region(image)
    
    # Save extracted images
    if card1_img.size > 0:
        extract_file = f"debug_extracted/hero_card_1_{timestamp}.png"
        cv2.imwrite(extract_file, card1_img)
        print(f"  ✅ Hero card 1 extracted to: {extract_file}")
        
        # Recognize card
        card = card_recognizer.recognize_single_card(card1_img, "hero_card1")
        if card:
            print(f"  ✅ Hero card 1: {card} (confidence: {card.confidence:.3f})")
        else:
            print(f"  ❌ Hero card 1: Not recognized")
    
    if card2_img.size > 0:
        extract_file = f"debug_extracted/hero_card_2_{timestamp}.png"
        cv2.imwrite(extract_file, card2_img)
        print(f"  ✅ Hero card 2 extracted to: {extract_file}")
        
        # Recognize card
        card = card_recognizer.recognize_single_card(card2_img, "hero_card2")
        if card:
            print(f"  ✅ Hero card 2: {card} (confidence: {card.confidence:.3f})")
        else:
            print(f"  ❌ Hero card 2: Not recognized")

if __name__ == "__main__":
    test_recognition()
