"""
Recognition System Manager
Centralized management of all card recognition systems with dynamic switching.
"""

import logging
import importlib
import sys
import os
from typing import Dict, Any, Optional, Type


class RecognitionSystemManager:
    """Manages multiple card recognition systems and allows dynamic switching."""
    
    def __init__(self):
        """Initialize the recognition system manager."""
        self.logger = logging.getLogger(__name__)
        
        # Available recognition systems
        self.available_systems = {
            'standard': {
                'module': 'src.card_recognizer',
                'class': 'CardRecognizer',
                'description': 'Basic template matching system',
                'features': ['template_matching', 'ocr_fallback']
            },
            'improved': {
                'module': 'improved_card_recognition',
                'class': 'ImprovedCardRecognizer',
                'description': 'Enhanced template matching with color analysis',
                'features': ['template_matching', 'color_analysis', 'empty_slot_detection', 'duplicate_prevention']
            },
            'enhanced': {
                'module': 'enhanced_card_recognition',
                'class': 'EnhancedCardRecognizer',
                'description': 'Color-based suit detection with template matching',
                'features': ['template_matching', 'color_suit_detection', 'confidence_boosting']
            },
            'comprehensive': {
                'module': 'comprehensive_card_recognition',
                'class': 'ComprehensiveCardRecognizer',
                'description': 'Multi-method recognition with robust validation',
                'features': ['template_matching', 'empty_slot_detection', 'color_analysis', 'validation']
            },
            'direct': {
                'module': 'direct_card_recognition',
                'class': 'DirectCardRecognizer',
                'description': 'Direct color and OCR-based recognition',
                'features': ['color_detection', 'ocr_recognition', 'shape_analysis', 'duplicate_prevention']
            },
            'color_based': {
                'module': 'color_based_card_recognizer',
                'class': 'ColorBasedCardRecognizer',
                'description': 'Four-color deck recognition system',
                'features': ['four_color_detection', 'template_matching', 'rank_detection']
            }
        }
        
        # Currently loaded system
        self.current_system = None
        self.current_system_name = None
        
        # System instances cache
        self.system_instances = {}
        
        self.logger.info(f"Recognition system manager initialized with {len(self.available_systems)} systems")
    
    def get_available_systems(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all available recognition systems."""
        return self.available_systems.copy()
    
    def load_system(self, system_name: str, force_reload: bool = False) -> Optional[Any]:
        """
        Load a specific recognition system.
        
        Args:
            system_name: Name of the system to load
            force_reload: Whether to force reload even if already loaded
            
        Returns:
            Recognition system instance or None if failed
        """
        if system_name not in self.available_systems:
            self.logger.error(f"Unknown recognition system: {system_name}")
            return None
        
        # Return cached instance if available and not forcing reload
        if not force_reload and system_name in self.system_instances:
            self.current_system = self.system_instances[system_name]
            self.current_system_name = system_name
            self.logger.info(f"Using cached {system_name} recognition system")
            return self.current_system
        
        try:
            system_info = self.available_systems[system_name]
            
            # Import the module
            module_name = system_info['module']
            class_name = system_info['class']
            
            # Add current directory to path if needed
            if not any(path.endswith('src') for path in sys.path):
                sys.path.append('src')
            
            # Import module
            if module_name.startswith('src.'):
                module = importlib.import_module(module_name)
            else:
                # Try importing from current directory
                spec = importlib.util.spec_from_file_location(module_name, f"{module_name}.py")
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                else:
                    module = importlib.import_module(module_name)
            
            # Get the class
            recognizer_class = getattr(module, class_name)
            
            # Create instance
            recognizer_instance = recognizer_class()
            
            # Cache the instance
            self.system_instances[system_name] = recognizer_instance
            self.current_system = recognizer_instance
            self.current_system_name = system_name
            
            self.logger.info(f"Successfully loaded {system_name} recognition system")
            return recognizer_instance
            
        except Exception as e:
            self.logger.error(f"Failed to load {system_name} recognition system: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
    def switch_system(self, new_system_name: str) -> bool:
        """
        Switch to a different recognition system.
        
        Args:
            new_system_name: Name of the system to switch to
            
        Returns:
            True if switch was successful, False otherwise
        """
        if new_system_name == self.current_system_name:
            self.logger.info(f"Already using {new_system_name} recognition system")
            return True
        
        old_system = self.current_system_name
        new_system = self.load_system(new_system_name)
        
        if new_system:
            self.logger.info(f"Switched from {old_system} to {new_system_name} recognition system")
            return True
        else:
            self.logger.error(f"Failed to switch to {new_system_name} recognition system")
            return False
    
    def get_current_system(self) -> Optional[Any]:
        """Get the currently loaded recognition system."""
        return self.current_system
    
    def get_current_system_name(self) -> Optional[str]:
        """Get the name of the currently loaded recognition system."""
        return self.current_system_name
    
    def get_system_features(self, system_name: str) -> list:
        """Get the features of a specific recognition system."""
        if system_name in self.available_systems:
            return self.available_systems[system_name]['features']
        return []
    
    def test_system(self, system_name: str, test_image_path: str = None) -> Dict[str, Any]:
        """
        Test a recognition system with optional test image.
        
        Args:
            system_name: Name of the system to test
            test_image_path: Optional path to test image
            
        Returns:
            Test results dictionary
        """
        system = self.load_system(system_name)
        if not system:
            return {'success': False, 'error': 'Failed to load system'}
        
        try:
            import cv2
            import time
            
            # Use test image or create a simple test
            if test_image_path and os.path.exists(test_image_path):
                test_img = cv2.imread(test_image_path)
            else:
                # Create a simple test image
                test_img = cv2.imread('card_templates/A_hearts.png')
                if test_img is None:
                    # Create a basic test image
                    import numpy as np
                    test_img = np.ones((100, 80, 3), dtype=np.uint8) * 255
            
            if test_img is None:
                return {'success': False, 'error': 'No test image available'}
            
            # Test recognition
            start_time = time.time()
            
            if hasattr(system, 'recognize_card'):
                result = system.recognize_card(test_img, debug=False)
            else:
                return {'success': False, 'error': 'System does not have recognize_card method'}
            
            end_time = time.time()
            
            # Analyze result
            test_results = {
                'success': True,
                'system_name': system_name,
                'recognition_time': end_time - start_time,
                'result': result,
                'features_available': self.get_system_features(system_name)
            }
            
            # Check if result is valid
            if result:
                if isinstance(result, tuple):
                    card_code, confidence, method = result
                    test_results['card_detected'] = card_code not in ('empty', 'error', 'unknown')
                    test_results['confidence'] = confidence
                    test_results['method'] = method
                elif isinstance(result, dict):
                    test_results['card_detected'] = not result.get('is_empty', True)
                    test_results['confidence'] = result.get('confidence', 0.0)
                    test_results['method'] = result.get('method', 'unknown')
                else:
                    test_results['card_detected'] = result is not None
                    test_results['confidence'] = 0.0
                    test_results['method'] = 'unknown'
            else:
                test_results['card_detected'] = False
                test_results['confidence'] = 0.0
                test_results['method'] = 'none'
            
            return test_results
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'system_name': system_name
            }
    
    def benchmark_all_systems(self, test_image_path: str = None) -> Dict[str, Dict[str, Any]]:
        """
        Benchmark all available recognition systems.
        
        Args:
            test_image_path: Optional path to test image
            
        Returns:
            Dictionary with results for each system
        """
        results = {}
        
        for system_name in self.available_systems.keys():
            self.logger.info(f"Benchmarking {system_name} recognition system...")
            results[system_name] = self.test_system(system_name, test_image_path)
        
        return results
    
    def get_best_system(self, criteria: str = 'accuracy') -> Optional[str]:
        """
        Determine the best recognition system based on criteria.
        
        Args:
            criteria: 'accuracy', 'speed', or 'balanced'
            
        Returns:
            Name of the best system or None
        """
        benchmark_results = self.benchmark_all_systems()
        
        best_system = None
        best_score = 0
        
        for system_name, results in benchmark_results.items():
            if not results['success']:
                continue
            
            if criteria == 'accuracy':
                score = results.get('confidence', 0.0)
            elif criteria == 'speed':
                score = 1.0 / max(results.get('recognition_time', 1.0), 0.001)
            elif criteria == 'balanced':
                confidence = results.get('confidence', 0.0)
                speed = 1.0 / max(results.get('recognition_time', 1.0), 0.001)
                score = (confidence * 0.7) + (min(speed, 10) / 10 * 0.3)
            else:
                score = results.get('confidence', 0.0)
            
            if score > best_score:
                best_score = score
                best_system = system_name
        
        self.logger.info(f"Best system for {criteria}: {best_system} (score: {best_score:.3f})")
        return best_system
    
    def cleanup(self):
        """Cleanup loaded systems."""
        for system_name, system_instance in self.system_instances.items():
            try:
                if hasattr(system_instance, 'cleanup'):
                    system_instance.cleanup()
            except Exception as e:
                self.logger.error(f"Error cleaning up {system_name}: {e}")
        
        self.system_instances.clear()
        self.current_system = None
        self.current_system_name = None
        
        self.logger.info("Recognition systems cleaned up")