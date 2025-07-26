"""
Test script to detect empty card slots vs actual cards
This script analyzes card images to determine if they contain actual cards or are empty slots
"""

import os
import sys
import cv2
import numpy as np
import logging
import argparse
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('empty_card_detector')

def analyze_card_image(image_path):
    """Analyze an image to determine if it contains a card or is an empty slot."""
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        logger.error(f"Failed to load image: {image_path}")
        return None
    
    # Get image dimensions
    height, width = image.shape[:2]
    logger.info(f"Image dimensions: {width}x{height}")
    
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply edge detection
    edges = cv2.Canny(gray, 50, 150)
    
    # Count edge pixels
    edge_count = np.count_nonzero(edges)
    edge_percentage = (edge_count / (width * height)) * 100
    
    # Measure standard deviation of pixel values (measure of contrast)
    std_dev = np.std(gray)
    
    # Check color variation - convert to HSV and measure standard deviation
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    h_std = np.std(hsv[:,:,0])
    s_std = np.std(hsv[:,:,1])
    
    # Create feature vector
    features = {
        'edge_percentage': edge_percentage,
        'std_dev': std_dev,
        'h_std': h_std,
        's_std': s_std
    }
    
    # Decision logic
    # Cards usually have more edges, higher contrast, and more color variation
    is_card = (edge_percentage > 5.0 or std_dev > 30.0 or h_std > 10.0 or s_std > 20.0)
    
    # Check if the image is too small (handle very small extracted cards)
    min_size = 30
    if width < min_size or height < min_size:
        # Resize for better visualization
        scale_factor = max(min_size / width, min_size / height)
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_NEAREST)
        edges = cv2.resize(edges, (new_width, new_height), interpolation=cv2.INTER_NEAREST)
        width, height = new_width, new_height

    # Create visualization with fixed size text area
    text_width = max(width, 100)  # Ensure text area has minimum width
    vis_width = width * 2 + text_width
    visualization = np.zeros((height, vis_width, 3), dtype=np.uint8)
    
    # Original image
    visualization[:, :width] = image
    
    # Edge image (convert to color)
    edge_vis = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    visualization[:, width:width*2] = edge_vis
    
    # Add text area
    text_area = np.ones((height, text_width, 3), dtype=np.uint8) * 255
    
    # Add feature text
    font = cv2.FONT_HERSHEY_SIMPLEX
    y_pos = 20
    cv2.putText(text_area, f"Edges: {edge_percentage:.1f}%", (10, y_pos), font, 0.4, (0, 0, 0), 1)
    y_pos += 15
    cv2.putText(text_area, f"Contrast: {std_dev:.1f}", (10, y_pos), font, 0.4, (0, 0, 0), 1)
    y_pos += 15
    cv2.putText(text_area, f"Hue var: {h_std:.1f}", (10, y_pos), font, 0.4, (0, 0, 0), 1)
    y_pos += 15
    cv2.putText(text_area, f"Sat var: {s_std:.1f}", (10, y_pos), font, 0.4, (0, 0, 0), 1)
    
    # Add result
    y_pos += 20
    result_text = "CARD DETECTED" if is_card else "EMPTY SLOT"
    result_color = (0, 200, 0) if is_card else (0, 0, 200)
    cv2.putText(text_area, result_text, (10, y_pos), font, 0.5, result_color, 1)
    
    # Add to visualization
    visualization[:, width*2:] = text_area
    
    # Add section labels
    cv2.putText(visualization, "Original", (10, 10), font, 0.4, (255, 255, 255), 1)
    cv2.putText(visualization, "Edges", (width + 10, 10), font, 0.4, (255, 255, 255), 1)
    cv2.putText(visualization, "Analysis", (width*2 + 10, 10), font, 0.4, (0, 0, 0), 1)
    
    # Save visualization
    output_dir = "debug_cards/empty_detection"
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.basename(image_path)
    output_path = os.path.join(output_dir, f"analysis_{base_name}")
    cv2.imwrite(output_path, visualization)
    
    logger.info(f"Analysis results for {base_name}:")
    logger.info(f"  Edge percentage: {edge_percentage:.2f}%")
    logger.info(f"  Contrast (std dev): {std_dev:.2f}")
    logger.info(f"  Hue variation: {h_std:.2f}")
    logger.info(f"  Saturation variation: {s_std:.2f}")
    logger.info(f"  Result: {'CARD DETECTED' if is_card else 'EMPTY SLOT'}")
    
    return {
        'image_path': image_path,
        'features': features,
        'is_card': is_card,
        'visualization_path': output_path
    }

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Detect empty card slots vs actual cards')
    parser.add_argument('--image', help='Path to card image to analyze')
    parser.add_argument('--directory', help='Path to directory of card images to analyze')
    args = parser.parse_args()
    
    if args.image:
        # Analyze single image
        result = analyze_card_image(args.image)
        if result:
            print(f"\nResult: {'CARD DETECTED' if result['is_card'] else 'EMPTY SLOT'}")
            print(f"Visualization saved to: {result['visualization_path']}")
    
    elif args.directory:
        # Analyze all images in directory
        if not os.path.exists(args.directory):
            logger.error(f"Directory not found: {args.directory}")
            return
        
        image_files = [f for f in os.listdir(args.directory) 
                      if f.lower().endswith(('.png', '.jpg', '.jpeg')) 
                      and f.startswith(('extracted_', 'hero_card'))]
        
        if not image_files:
            logger.error(f"No image files found in {args.directory}")
            return
            
        logger.info(f"Analyzing {len(image_files)} images in {args.directory}")
        
        card_count = 0
        empty_count = 0
        
        for image_file in image_files:
            image_path = os.path.join(args.directory, image_file)
            result = analyze_card_image(image_path)
            
            if result:
                if result['is_card']:
                    card_count += 1
                else:
                    empty_count += 1
        
        logger.info(f"\nAnalysis complete:")
        logger.info(f"  Total images: {len(image_files)}")
        logger.info(f"  Cards detected: {card_count}")
        logger.info(f"  Empty slots: {empty_count}")
        logger.info(f"  Empty percentage: {(empty_count / len(image_files)) * 100:.1f}%")
        
    else:
        print("Please specify either --image or --directory")
        parser.print_help()

if __name__ == "__main__":
    main()
