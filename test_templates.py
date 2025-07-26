#!/usr/bin/env python3
"""Test script to verify card template loading"""

import sys
import os
sys.path.append('src')

def test_template_loading():
    from card_recognizer import CardRecognizer
    
    # Check if templates exist
    template_dir = 'card_templates'
    if os.path.exists(template_dir):
        files = [f for f in os.listdir(template_dir) if f.endswith('.png')]
        print(f'Found {len(files)} template files')
        print('Sample files:', files[:5])
        
        # Test the recognizer
        print("Initializing CardRecognizer...")
        recognizer = CardRecognizer()
        stats = recognizer.get_recognition_stats()
        
        print(f'Templates loaded: {stats["templates_loaded"]}')
        print(f'Template matching enabled: {stats["template_matching_enabled"]}')
        
        if stats['templates_loaded'] > 0:
            print('✅ Template loading mapping working correctly!')
            # Show a few loaded templates
            template_keys = list(recognizer.card_templates.keys())[:10]
            print(f'Sample loaded templates: {template_keys}')
            
            # Show the mapping
            print("\nFile name -> Internal mapping examples:")
            for i, (key, template) in enumerate(recognizer.card_templates.items()):
                if i < 5:  # Show first 5
                    rank, suit = key[0], key[1]
                    suit_names = {'h': 'hearts', 'd': 'diamonds', 'c': 'clubs', 's': 'spades'}
                    rank_names = {'T': '10'}
                    
                    file_rank = rank_names.get(rank, rank)
                    file_suit = suit_names[suit]
                    
                    print(f"  {file_rank}_{file_suit}.png -> {key}")
        else:
            print('❌ No templates loaded - check file naming')
    else:
        print('❌ Template directory not found')

if __name__ == "__main__":
    test_template_loading()
