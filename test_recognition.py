#!/usr/bin/env python3
"""
Comprehensive test script for PokerStars Bot recognition system.
Tests all stages of card recognition and region calibration.
"""

import sys
import os
import logging
import json
import time
import cv2
import numpy as np
from typing import Dict, List, Optional

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from window_capture import PokerStarsWindowCapture
    from card_recognizer import CardRecognizer
    from community_card_detector import CommunityCardDetector
    from poker_table_analyzer import PokerTableAnalyzer
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

class BotTestSuite:
    """Comprehensive test suite for the poker bot recognition system."""
    
    def __init__(self):
        """Initialize the test suite."""
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('test_recognition.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.logger.info("Initializing bot components...")
        self.window_capture = PokerStarsWindowCapture()
        self.card_recognizer = CardRecognizer()
        self.community_detector = CommunityCardDetector(self.card_recognizer)
        self.table_analyzer = PokerTableAnalyzer()
        
        # Test results storage
        self.test_results = {}
        
    def test_window_detection(self) -> bool:
        """Test 1: Window Detection and Capture"""
        self.logger.info("\n" + "="*50)
        self.logger.info("TEST 1: Window Detection and Capture")
        self.logger.info("="*50)
        
        try:
            # Find PokerStars windows
            windows = self.window_capture.find_pokerstars_windows()
            
            if not windows:
                self.logger.error("❌ No PokerStars windows found!")
                return False
            
            self.logger.info(f"✅ Found {len(windows)} PokerStars windows:")
            for i, window in enumerate(windows):
                self.logger.info(f"  {i+1}. {window['title']} ({window['width']}x{window['height']}) Score: {window.get('score', 'N/A')}")
            
            # Select the best window
            best_window = self.window_capture.select_best_window()
            if not best_window:
                self.logger.error("❌ Failed to select best window!")
                return False
            
            self.logger.info(f"✅ Selected: {best_window['title']}")
            
            # Test capture
            frame = self.window_capture.capture_frame()
            if frame is None:
                self.logger.error("❌ Failed to capture frame!")
                return False
            
            # Save test capture
            os.makedirs("test_output", exist_ok=True)
            cv2.imwrite("test_output/window_capture_test.png", frame)
            self.logger.info(f"✅ Captured frame: {frame.shape} saved to test_output/window_capture_test.png")
            
            self.test_results['window_detection'] = {
                'success': True,
                'windows_found': len(windows),
                'selected_window': best_window['title'],
                'frame_shape': frame.shape
            }
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Window detection test failed: {e}")
            self.test_results['window_detection'] = {'success': False, 'error': str(e)}
            return False
    
    def test_region_configuration(self) -> bool:
        """Test 2: Region Configuration Loading"""
        self.logger.info("\n" + "="*50)
        self.logger.info("TEST 2: Region Configuration")
        self.logger.info("="*50)
        
        try:
            # Check if region config exists
            config_path = "region_config.json"
            if not os.path.exists(config_path):
                self.logger.warning("⚠️  No region configuration found, using defaults")
                # Create default regions
                default_regions = {
                    'hero_card_1': {'x': 42.0, 'y': 72.0, 'width': 5.5, 'height': 6.0},
                    'hero_card_2': {'x': 48.5, 'y': 72.0, 'width': 5.5, 'height': 6.0},
                    'community_card_1': {'x': 33.5, 'y': 35.0, 'width': 6.0, 'height': 8.0},
                    'community_card_2': {'x': 40.5, 'y': 35.0, 'width': 6.0, 'height': 8.0},
                    'community_card_3': {'x': 47.5, 'y': 35.0, 'width': 6.0, 'height': 8.0},
                    'community_card_4': {'x': 54.5, 'y': 35.0, 'width': 6.0, 'height': 8.0},
                    'community_card_5': {'x': 61.5, 'y': 35.0, 'width': 6.0, 'height': 8.0},
                    'pot_area': {'x': 43.0, 'y': 42.0, 'width': 14.0, 'height': 6.0}
                }
                
                with open(config_path, 'w') as f:
                    json.dump(default_regions, f, indent=2)
                self.logger.info(f"✅ Created default region configuration")
            
            # Load and validate regions
            with open(config_path, 'r') as f:
                regions = json.load(f)
            
            self.logger.info(f"✅ Loaded {len(regions)} regions:")
            for name, region in regions.items():
                self.logger.info(f"  {name}: x={region['x']:.1f}%, y={region['y']:.1f}%, w={region['width']:.1f}%, h={region['height']:.1f}%")
            
            self.test_results['region_config'] = {
                'success': True,
                'regions_loaded': len(regions),
                'regions': list(regions.keys())
            }
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Region configuration test failed: {e}")
            self.test_results['region_config'] = {'success': False, 'error': str(e)}
            return False
    
    def test_card_template_loading(self) -> bool:
        """Test 3: Card Template Loading"""
        self.logger.info("\n" + "="*50)
        self.logger.info("TEST 3: Card Template Loading")
        self.logger.info("="*50)
        
        try:
            # Check template loading
            if not self.card_recognizer.template_loaded:
                self.logger.error("❌ Card templates not loaded!")
                return False
            
            template_count = len(self.card_recognizer.card_templates)
            self.logger.info(f"✅ Loaded {template_count} card templates")
            
            # Expected templates (52 cards)
            expected_cards = []
            ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
            suits = ['h', 'd', 'c', 's']
            
            for rank in ranks:
                for suit in suits:
                    expected_cards.append(f"{rank}{suit}")
            
            missing_cards = [card for card in expected_cards if card not in self.card_recognizer.card_templates]
            
            if missing_cards:
                self.logger.warning(f"⚠️  Missing {len(missing_cards)} card templates: {missing_cards[:10]}...")
            else:
                self.logger.info("✅ All 52 card templates loaded successfully")
            
            # Test a few template samples
            sample_templates = list(self.card_recognizer.card_templates.items())[:5]
            for card_name, template in sample_templates:
                if template is not None:
                    self.logger.info(f"  {card_name}: {template.shape}")
                else:
                    self.logger.warning(f"  {card_name}: Template is None!")
            
            self.test_results['template_loading'] = {
                'success': True,
                'templates_loaded': template_count,
                'missing_templates': len(missing_cards),
                'expected_total': 52
            }
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Template loading test failed: {e}")
            self.test_results['template_loading'] = {'success': False, 'error': str(e)}
            return False
    
    def test_card_recognition(self) -> bool:
        """Test 4: Live Card Recognition"""
        self.logger.info("\n" + "="*50)
        self.logger.info("TEST 4: Live Card Recognition")
        self.logger.info("="*50)
        
        try:
            # Capture current frame
            frame = self.window_capture.capture_frame()
            if frame is None:
                self.logger.error("❌ Failed to capture frame for recognition test!")
                return False
            
            # Test hole card recognition
            self.logger.info("Testing hole card recognition...")
            hole_cards = self.card_recognizer.recognize_hole_cards(frame)
            
            if hole_cards and hole_cards.is_valid():
                self.logger.info(f"✅ Hole cards detected: {hole_cards}")
            else:
                self.logger.warning("⚠️  No valid hole cards detected")
            
            # Test community card recognition
            self.logger.info("Testing community card recognition...")
            community_cards = self.community_detector.detect_community_cards(frame)
            
            if community_cards and community_cards.count > 0:
                visible_cards = [f"{card.rank}{card.suit}" for card in community_cards.cards if card is not None]
                self.logger.info(f"✅ Community cards detected ({community_cards.phase}): {visible_cards}")
            else:
                self.logger.info("ℹ️  No community cards detected (likely pre-flop)")
            
            # Save debug images
            cv2.imwrite("test_output/recognition_test_frame.png", frame)
            
            self.test_results['card_recognition'] = {
                'success': True,
                'hole_cards_valid': hole_cards.is_valid() if hole_cards else False,
                'community_cards_count': community_cards.count if community_cards else 0,
                'community_phase': community_cards.phase if community_cards else 'unknown'
            }
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Card recognition test failed: {e}")
            self.test_results['card_recognition'] = {'success': False, 'error': str(e)}
            return False
    
    def test_complete_analysis(self) -> bool:
        """Test 5: Complete Table Analysis"""
        self.logger.info("\n" + "="*50)
        self.logger.info("TEST 5: Complete Table Analysis")
        self.logger.info("="*50)
        
        try:
            # Capture current frame
            frame = self.window_capture.capture_frame()
            if frame is None:
                self.logger.error("❌ Failed to capture frame for analysis test!")
                return False
            
            # Run complete analysis
            analysis = self.table_analyzer.analyze_complete_table(frame)
            
            if analysis:
                self.logger.info("✅ Complete table analysis results:")
                self.logger.info(f"  Stakes: {analysis.get('stakes', 'Unknown')}")
                self.logger.info(f"  Pot Size: {analysis.get('pot_size_bb', 0)} BB")
                self.logger.info(f"  Game Phase: {analysis.get('game_phase', 'Unknown')}")
                self.logger.info(f"  Active Players: {len(analysis.get('players', []))}")
                
                # Show player details
                for i, player in enumerate(analysis.get('players', [])):
                    if player.get('active', False):
                        self.logger.info(f"  Player {i+1}: {player}")
                
                self.test_results['complete_analysis'] = {
                    'success': True,
                    'pot_detected': analysis.get('pot_size_bb', 0) > 0,
                    'players_detected': len(analysis.get('players', [])),
                    'game_phase': analysis.get('game_phase', 'unknown')
                }
                
                return True
            else:
                self.logger.warning("⚠️  Analysis returned no results")
                self.test_results['complete_analysis'] = {'success': False, 'error': 'No analysis results'}
                return False
            
        except Exception as e:
            self.logger.error(f"❌ Complete analysis test failed: {e}")
            self.test_results['complete_analysis'] = {'success': False, 'error': str(e)}
            return False
    
    def run_all_tests(self) -> Dict:
        """Run all tests and return results summary."""
        self.logger.info("\n" + "🎯 STARTING COMPREHENSIVE BOT TEST SUITE 🎯")
        self.logger.info("=" * 60)
        
        start_time = time.time()
        
        # Run all tests
        tests = [
            ('Window Detection', self.test_window_detection),
            ('Region Configuration', self.test_region_configuration),
            ('Template Loading', self.test_card_template_loading),
            ('Card Recognition', self.test_card_recognition),
            ('Complete Analysis', self.test_complete_analysis)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                success = test_func()
                if success:
                    passed_tests += 1
                    self.logger.info(f"✅ {test_name}: PASSED")
                else:
                    self.logger.error(f"❌ {test_name}: FAILED")
            except Exception as e:
                self.logger.error(f"💥 {test_name}: CRASHED - {e}")
        
        end_time = time.time()
        
        # Summary
        self.logger.info("\n" + "📊 TEST SUMMARY")
        self.logger.info("=" * 30)
        self.logger.info(f"Tests Passed: {passed_tests}/{total_tests}")
        self.logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        self.logger.info(f"Total Time: {end_time - start_time:.2f} seconds")
        
        if passed_tests == total_tests:
            self.logger.info("🎉 ALL TESTS PASSED! Bot is working correctly.")
        else:
            self.logger.warning(f"⚠️  {total_tests - passed_tests} tests failed. Check logs for details.")
        
        # Save results
        summary = {
            'timestamp': time.time(),
            'tests_passed': passed_tests,
            'tests_total': total_tests,
            'success_rate': (passed_tests/total_tests)*100,
            'duration': end_time - start_time,
            'detailed_results': self.test_results
        }
        
        with open('test_output/test_results.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        return summary

def main():
    """Main test runner."""
    print("🤖 PokerStars Bot Recognition Test Suite")
    print("=" * 40)
    
    # Create test suite
    test_suite = BotTestSuite()
    
    # Run tests
    results = test_suite.run_all_tests()
    
    # Exit with appropriate code
    if results['tests_passed'] == results['tests_total']:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print(f"\n❌ {results['tests_total'] - results['tests_passed']} tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
