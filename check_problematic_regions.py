import cv2
import numpy as np

# Load the test image to see what we're working with
img = cv2.imread('test_enhanced_capture_1754352826.png')
if img is not None:
    height, width = img.shape[:2]
    print(f'Current image: {width}x{height}')
    
    # Convert problematic regions to pixels to see where they're pointing
    regions = {
        'community_card_4': {'x': 52.08, 'y': 32.94, 'width': 3.68, 'height': 9.50},
        'community_card_5': {'x': 55.92, 'y': 32.94, 'width': 3.05, 'height': 9.12},
        'hero_card_1': {'x': 46.42, 'y': 59.65, 'width': 3.82, 'height': 7.31},
        'hero_card_2': {'x': 49.97, 'y': 60.02, 'width': 3.82, 'height': 6.94}
    }
    
    print('Problematic regions in pixels:')
    for name, region in regions.items():
        x = int((region['x'] / 100.0) * width)
        y = int((region['y'] / 100.0) * height)
        w = int((region['width'] / 100.0) * width)
        h = int((region['height'] / 100.0) * height)
        print(f'{name}: x={x}, y={y}, w={w}, h={h} (ends at x={x+w}, y={y+h})')
        
        # Extract and check region
        region_img = img[y:y+h, x:x+w]
        avg_color = np.mean(region_img, axis=(0,1))
        print(f'  Average color: BGR({avg_color[0]:.0f}, {avg_color[1]:.0f}, {avg_color[2]:.0f})')
        cv2.imwrite(f'debug_problematic_{name}.png', region_img)
else:
    print('Could not load test image')
