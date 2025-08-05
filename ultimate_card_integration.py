"""
Ultimate Card Integration System
Combines all available recognition methods for maximum accuracy and detailed logging
"""

import cv2
import numpy as np
import time
import logging
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass

@dataclass
class UltimateCardResult:
    """Enhanced card recognition result with detailed information"""
    region_name: str
    card_code: str  # "Aspades", "Khearts", etc.
    rank: str
    suit: str
    confidence: float
    method: str  # "Enhanced", "OCR", "Pattern", "Fallback"
    processing_time: float  # Time taken for recognition in seconds
    is_empty: bool = False
    error_message: Optional[str] = None
    
    def __str__(self):
        if self.is_empty:
            return f"{self.region_name}: EMPTY"
        elif self.card_code == 'error':
            return f"{self.region_name}: ERROR - {self.error_message}"
        else:
            return f"{self.region_name}: {self.card_code} (conf: {self.confidence:.3f}, {self.method}, {self.processing_time*1000:.1f}ms)"

class UltimateCardIntegration:
    """Ultimate card recognition system combining all available methods"""
    
    def __init__(self, debug_mode: bool = True):
        self.debug_mode = debug_mode
        self.logger = logging.getLogger("ultimate_card_integration")
        
        # Performance tracking
        self.recognition_stats = {
            'total_recognitions': 0,
            'successful_recognitions': 0,
            'failed_recognitions': 0,
            'empty_detections': 0,
            'average_processing_time': 0.0,
            'method_usage': {},
            'confidence_distribution': []
        }
        
        # Initialize recognition systems
        self.recognition_systems = {}
        self._initialize_recognition_systems()
        
        # Recognition settings
        self.min_confidence_threshold = 0.1
        self.empty_detection_threshold = 0.05
        
    def _initialize_recognition_systems(self):
        """Initialize all available recognition systems"""
        self.logger.info("Initializing Ultimate Card Recognition System...")
        
        # Try to load enhanced card recognition
        try:
            from enhanced_card_recognition import EnhancedCardRecognition
            self.recognition_systems['enhanced'] = EnhancedCardRecognition(debug_mode=self.debug_mode)
            self.logger.info("✅ Enhanced Card Recognition loaded")
        except ImportError as e:
            self.logger.warning(f"Enhanced Card Recognition not available: {e}")
        
        # Try to load enhanced OCR recognition
        try:
            from enhanced_ocr_recognition import EnhancedOCRCardRecognition
            self.recognition_systems['ocr'] = EnhancedOCRCardRecognition()
            self.logger.info("✅ Enhanced OCR Recognition loaded")
        except ImportError as e:
            self.logger.warning(f"Enhanced OCR Recognition not available: {e}")
        
        # Try to load fallback recognition
        try:
            from fallback_card_recognition import FallbackCardRecognition
            self.recognition_systems['fallback'] = FallbackCardRecognition()
            self.logger.info("✅ Fallback Card Recognition loaded")
        except ImportError as e:
            self.logger.warning(f"Fallback Card Recognition not available: {e}")
        
        if not self.recognition_systems:
            self.logger.error("❌ No recognition systems available!")
        else:
            self.logger.info(f"✅ Ultimate Card Integration initialized with {len(self.recognition_systems)} recognition systems")
    
    def recognize_all_cards(self, screenshot: np.ndarray, regions: Dict[str, Dict] = None, use_cache: bool = True) -> List[UltimateCardResult]:
        """
        Recognize all cards in the screenshot using available regions
        
        Args:
            screenshot: Full screenshot image
            regions: Dictionary of region definitions {name: {x, y, width, height}}
            use_cache: Whether to use cached results for performance
            
        Returns:
            List of UltimateCardResult objects with detailed information
        """
        start_time = time.time()
        results = []
        
        if regions is None:
            self.logger.warning("No regions provided for card recognition")
            return results
        
        self.logger.info(f"🎯 Starting Ultimate Card Recognition on {len(regions)} regions...")
        
        # Process each region
        for region_name, region_data in regions.items():
            result = self._recognize_single_card(screenshot, region_name, region_data)
            results.append(result)
            
            # Log individual result
            if result.is_empty:
                self.logger.debug(f"   {region_name}: EMPTY")
            elif result.card_code == 'error':
                self.logger.warning(f"   {region_name}: ERROR - {result.error_message}")
            else:
                self.logger.info(f"   {region_name}: {result.card_code} (conf: {result.confidence:.3f}, {result.method}, {result.processing_time*1000:.1f}ms)")
        
        # Update statistics
        total_time = time.time() - start_time
        self._update_recognition_stats(results, total_time)
        
        self.logger.info(f"🎯 Ultimate Card Recognition completed in {total_time*1000:.1f}ms")
        
        return results
    
    def _recognize_single_card(self, screenshot: np.ndarray, region_name: str, region_data: Dict) -> UltimateCardResult:
        """Recognize a single card from a region with detailed error handling"""
        start_time = time.time()
        
        try:
            # Extract region from screenshot
            x = region_data.get('x', 0)
            y = region_data.get('y', 0)
            w = region_data.get('width', 0)
            h = region_data.get('height', 0)
            
            # Validate region bounds
            height, width = screenshot.shape[:2]
            if x < 0 or y < 0 or x + w > width or y + h > height:
                return UltimateCardResult(
                    region_name=region_name,
                    card_code='error',
                    rank='?',
                    suit='?',
                    confidence=0.0,
                    method='Validation',
                    processing_time=time.time() - start_time,
                    is_empty=False,
                    error_message=f"Invalid region bounds: ({x}, {y}, {w}, {h}) for image {width}x{height}"
                )
            
            # Extract region image
            region_img = screenshot[y:y+h, x:x+w]
            
            if region_img.size == 0:
                return UltimateCardResult(
                    region_name=region_name,
                    card_code='error',
                    rank='?',
                    suit='?',
                    confidence=0.0,
                    method='Extraction',
                    processing_time=time.time() - start_time,
                    is_empty=False,
                    error_message="Empty region extracted"
                )
            
            # Check if region appears to be empty (mostly green table)
            if self._is_empty_region(region_img):
                return UltimateCardResult(
                    region_name=region_name,
                    card_code='empty',
                    rank='',
                    suit='',
                    confidence=0.0,
                    method='EmptyDetection',
                    processing_time=time.time() - start_time,
                    is_empty=True
                )
            
            # Try recognition with all available systems
            best_result = self._try_all_recognition_methods(region_img, region_name)
            
            if best_result:
                return UltimateCardResult(
                    region_name=region_name,
                    card_code=f"{best_result['rank']}{best_result['suit']}",
                    rank=best_result['rank'],
                    suit=best_result['suit'],
                    confidence=best_result['confidence'],
                    method=best_result['method'],
                    processing_time=time.time() - start_time,
                    is_empty=False
                )
            else:
                return UltimateCardResult(
                    region_name=region_name,
                    card_code='error',
                    rank='?',
                    suit='?',
                    confidence=0.0,
                    method='AllFailed',
                    processing_time=time.time() - start_time,
                    is_empty=False,
                    error_message="All recognition methods failed"
                )
                
        except Exception as e:
            return UltimateCardResult(
                region_name=region_name,
                card_code='error',
                rank='?',
                suit='?',
                confidence=0.0,
                method='Exception',
                processing_time=time.time() - start_time,
                is_empty=False,
                error_message=str(e)
            )
    
    def _is_empty_region(self, region_img: np.ndarray) -> bool:
        """Check if region appears to be empty (mostly green table)"""
        try:
            # Calculate average color
            avg_color = np.mean(region_img, axis=(0, 1))
            
            # Check if it's predominantly green (poker table color)
            # BGR format: avg_color[0] = Blue, avg_color[1] = Green, avg_color[2] = Red
            is_green_dominant = (avg_color[1] > avg_color[0] and 
                               avg_color[1] > avg_color[2] and 
                               avg_color[1] > 80)
            
            # Check if colors are too uniform (not enough variation for a card)
            color_variance = np.var(region_img)
            is_too_uniform = color_variance < 100
            
            return is_green_dominant or is_too_uniform
            
        except Exception as e:
            self.logger.warning(f"Empty region detection failed: {e}")
            return False
    
    def _try_all_recognition_methods(self, region_img: np.ndarray, region_name: str) -> Optional[Dict]:
        """Try all available recognition methods and return the best result"""
        results = []
        
        # Try each recognition system
        for system_name, system in self.recognition_systems.items():
            try:
                result = self._try_recognition_system(system, system_name, region_img)
                if result and result.get('confidence', 0) >= self.min_confidence_threshold:
                    results.append(result)
            except Exception as e:
                self.logger.warning(f"{system_name} recognition failed for {region_name}: {e}")
        
        # Return best result based on confidence
        if results:
            best_result = max(results, key=lambda r: r.get('confidence', 0))
            return best_result
        
        return None
    
    def _try_recognition_system(self, system: Any, system_name: str, region_img: np.ndarray) -> Optional[Dict]:
        """Try a specific recognition system"""
        try:
            if system_name == 'enhanced':
                # Enhanced card recognition
                result = system.recognize_card(
                    region_img, 
                    region=(0, 0, region_img.shape[1], region_img.shape[0]),
                    four_color_deck=True
                )
                if result and hasattr(result, 'confidence') and result.confidence > 0:
                    return {
                        'rank': result.rank,
                        'suit': result.suit,
                        'confidence': result.confidence,
                        'method': f"Enhanced-{getattr(result, 'method', 'Unknown')}"
                    }
            
            elif system_name == 'ocr':
                # Enhanced OCR recognition
                result = system.recognize_card(region_img, debug=self.debug_mode)
                if result and hasattr(result, 'confidence') and result.confidence > 0:
                    return {
                        'rank': result.rank,
                        'suit': result.suit,
                        'confidence': result.confidence,
                        'method': "OCR"
                    }
            
            elif system_name == 'fallback':
                # Fallback recognition
                result = system.recognize_card(region_img, four_color_deck=True)
                if result and hasattr(result, 'confidence') and result.confidence > 0:
                    return {
                        'rank': result.rank,
                        'suit': result.suit,
                        'confidence': result.confidence,
                        'method': "Pattern"
                    }
            
        except Exception as e:
            self.logger.debug(f"{system_name} recognition error: {e}")
        
        return None
    
    def _update_recognition_stats(self, results: List[UltimateCardResult], total_time: float):
        """Update performance statistics"""
        self.recognition_stats['total_recognitions'] += len(results)
        
        successful = sum(1 for r in results if not r.is_empty and r.card_code != 'error')
        failed = sum(1 for r in results if r.card_code == 'error')
        empty = sum(1 for r in results if r.is_empty)
        
        self.recognition_stats['successful_recognitions'] += successful
        self.recognition_stats['failed_recognitions'] += failed
        self.recognition_stats['empty_detections'] += empty
        
        # Update processing time average
        total_recognitions = self.recognition_stats['total_recognitions']
        if total_recognitions > 0:
            old_avg = self.recognition_stats['average_processing_time']
            self.recognition_stats['average_processing_time'] = (
                (old_avg * (total_recognitions - len(results)) + total_time) / total_recognitions
            )
        
        # Update method usage
        for result in results:
            if not result.is_empty and result.card_code != 'error':
                method = result.method
                self.recognition_stats['method_usage'][method] = self.recognition_stats['method_usage'].get(method, 0) + 1
        
        # Update confidence distribution
        confidences = [r.confidence for r in results if not r.is_empty and r.card_code != 'error']
        self.recognition_stats['confidence_distribution'].extend(confidences)
        
        # Keep only last 100 confidence values
        if len(self.recognition_stats['confidence_distribution']) > 100:
            self.recognition_stats['confidence_distribution'] = self.recognition_stats['confidence_distribution'][-100:]
    
    def get_performance_stats(self) -> str:
        """Get formatted performance statistics"""
        stats = self.recognition_stats
        total = stats['total_recognitions']
        
        if total == 0:
            return "No recognition attempts yet"
        
        success_rate = (stats['successful_recognitions'] / total) * 100
        empty_rate = (stats['empty_detections'] / total) * 100
        failure_rate = (stats['failed_recognitions'] / total) * 100
        
        avg_confidence = 0.0
        if stats['confidence_distribution']:
            avg_confidence = sum(stats['confidence_distribution']) / len(stats['confidence_distribution'])
        
        result = []
        result.append(f"Success: {success_rate:.1f}% ({stats['successful_recognitions']}/{total})")
        result.append(f"Empty: {empty_rate:.1f}%")
        result.append(f"Failed: {failure_rate:.1f}%")
        result.append(f"Avg Time: {stats['average_processing_time']*1000:.1f}ms")
        result.append(f"Avg Conf: {avg_confidence:.3f}")
        
        # Method usage
        if stats['method_usage']:
            method_stats = []
            for method, count in stats['method_usage'].items():
                method_stats.append(f"{method}: {count}")
            result.append(f"Methods: {', '.join(method_stats)}")
        
        return " | ".join(result)
    
    def set_debug_mode(self, debug_mode: bool):
        """Enable or disable debug mode"""
        self.debug_mode = debug_mode
        
        # Update all recognition systems
        for system in self.recognition_systems.values():
            if hasattr(system, 'debug_mode'):
                system.debug_mode = debug_mode
    
    def get_detailed_log_entries(self, results: List[UltimateCardResult]) -> List[str]:
        """Generate detailed log entries for UI display"""
        log_entries = []
        
        # Summary
        successful = sum(1 for r in results if not r.is_empty and r.card_code != 'error')
        empty = sum(1 for r in results if r.is_empty)
        errors = sum(1 for r in results if r.card_code == 'error')
        
        log_entries.append(f"🎯 Recognition Summary: {successful} cards, {empty} empty, {errors} errors")
        
        # Individual card results
        for result in results:
            if not result.is_empty and result.card_code != 'error':
                time_str = f"{result.processing_time*1000:.1f}ms"
                conf_str = f"{result.confidence:.3f}"
                log_entries.append(f"   {result.region_name}: {result.card_code} (conf: {conf_str}, {result.method}, {time_str})")
            elif result.is_empty:
                log_entries.append(f"   {result.region_name}: EMPTY")
            else:
                log_entries.append(f"   {result.region_name}: ERROR - {result.error_message}")
        
        # Performance stats
        log_entries.append(f"📊 Performance: {self.get_performance_stats()}")
        
        return log_entries

def create_ultimate_integration() -> Optional[UltimateCardIntegration]:
    """Factory function to create ultimate card integration system"""
    try:
        return UltimateCardIntegration(debug_mode=True)
    except Exception as e:
        logging.getLogger("ultimate_card_integration").error(f"Failed to create ultimate integration: {e}")
        return None

if __name__ == "__main__":
    # Test the ultimate integration system
    logging.basicConfig(level=logging.INFO)
    
    ultimate_system = create_ultimate_integration()
    if ultimate_system:
        print("✅ Ultimate Card Integration System created successfully")
        print(f"📊 Available recognition systems: {list(ultimate_system.recognition_systems.keys())}")
    else:
        print("❌ Failed to create Ultimate Card Integration System")
