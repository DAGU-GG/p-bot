@@ .. @@
     def recognize_hero_hole_cards(self, table_image, debug=False):
         """
         Recognize hero's hole cards from the table image.
         This method implements the same interface as the original CardRecognizer.
         
         Args:
             table_image: Full table image
             debug: Whether to enable debug mode
             
         Returns:
             HoleCards: Object containing the recognized hole cards
         """
         try:
             from src.card_recognizer import HoleCards
         except ImportError:
             try:
                 import sys
                 sys.path.append("src")
                 from card_recognizer import HoleCards
             except ImportError:
                 self.logger.error("Cannot import HoleCards class - critical error")
                 class HoleCards:
                     def __init__(self): self.cards = [None, None]
                     def is_valid(self): return False
                     def __str__(self): return "Unknown"
         
         self.logger.info("IMPROVED SYSTEM: Recognizing hero hole cards")
         
         # Debug: Log current regions
         self.logger.info(f"Available card regions: {list(self.card_regions.keys()) if self.card_regions else 'None'}")
         
         # Extract card regions using original code to maintain compatibility
         card1_img, card2_img = None, None
         
         # Use the regions defined in the original recognizer
         if not hasattr(self, 'card_regions') or not self.card_regions:
             self.logger.warning("No card regions defined - cannot recognize hole cards")
             return HoleCards()
         
         # Extract card images using the regions
         try:
             height, width = table_image.shape[:2]
             self.logger.info(f"Processing table image: {width}x{height}")
             
             # Extract first card
             if 'hero_card1' in self.card_regions:
            # CRITICAL FIX: If template matching failed, try direct template matching
            if card_code in ('empty', 'error', 'unknown') or confidence < 0.3:
                self.logger.info("Template matching failed or low confidence, trying direct template matching...")
                try:
                    # Use the original recognizer's template matching directly
                    template_card = self.card_recognizer.recognize_card_by_template_matching(card_img, debug)
                    if template_card and hasattr(template_card, 'rank') and hasattr(template_card, 'suit'):
                        card_code = f"{template_card.rank}{template_card.suit}"
                        confidence = getattr(template_card, 'confidence', 0.7)
                        method = "direct_template_matching"
                        self.logger.info(f"Direct template matching succeeded: {card_code} (confidence: {confidence:.3f})")
                    else:
                        self.logger.warning("Direct template matching also failed")
                except Exception as e:
                    self.logger.error(f"Error in direct template matching: {e}")
            
            # CRITICAL FIX: If still no card detected, try OCR as final fallback
            if card_code in ('empty', 'error', 'unknown') or confidence < 0.3:
                self.logger.info("Trying OCR as final fallback...")
                try:
                    ocr_card = self.card_recognizer.recognize_card_by_ocr(card_img)
                    if ocr_card and hasattr(ocr_card, 'rank') and hasattr(ocr_card, 'suit'):
                        card_code = f"{ocr_card.rank}{ocr_card.suit}"
                        confidence = getattr(ocr_card, 'confidence', 0.5)
                        method = "ocr_fallback"
                        self.logger.info(f"OCR fallback succeeded: {card_code} (confidence: {confidence:.3f})")
                    else:
                        self.logger.warning("OCR fallback also failed")
                except Exception as e:
                    self.logger.error(f"Error in OCR fallback: {e}")
            
                 region = self.card_regions['hero_card1']
                 # Handle both percentage and decimal formats - check multiple possible keys
                 x_val = region.get('x', region.get('x_percent', 0))
                 y_val = region.get('y', region.get('y_percent', 0))
                 w_val = region.get('width', region.get('w', region.get('width_percent', 0)))
                 h_val = region.get('height', region.get('h', region.get('height_percent', 0)))
                 
                 # Convert percentage values to decimals if they're greater than 1
                 if x_val > 1:
                     x_val = x_val / 100.0
                 if y_val > 1:
                     y_val = y_val / 100.0
                 if w_val > 1:
                     w_val = w_val / 100.0
                 if h_val > 1:
                     h_val = h_val / 100.0
                 
                 # Convert to pixels
                 x = int(width * x_val)
                 y = int(height * y_val)
                 w = int(width * w_val)
                 h = int(height * h_val)
                 
                 self.logger.info(f"Hero card 1 region: x={x}, y={y}, w={w}, h={h} (from {x_val:.4f}, {y_val:.4f}, {w_val:.4f}, {h_val:.4f})")
                 if x >= 0 and y >= 0 and w > 0 and h > 0 and x + w <= width and y + h <= height:
                     card1_img = table_image[y:y+h, x:x+w]
                     if debug:
                         cv2.imwrite("debug_cards/improved/hero_card1.png", card1_img)
                         self.logger.info("Saved hero card 1 debug image")
                 else:
                     self.logger.warning(f"Hero card 1 region out of bounds: x={x}, y={y}, w={w}, h={h}")
             
             # Extract second card
             if 'hero_card2' in self.card_regions:
                 region = self.card_regions['hero_card2']
                 # Handle both percentage and decimal formats - check multiple possible keys
                 x_val = region.get('x', region.get('x_percent', 0))
                 y_val = region.get('y', region.get('y_percent', 0))
                 w_val = region.get('width', region.get('w', region.get('width_percent', 0)))
                 h_val = region.get('height', region.get('h', region.get('height_percent', 0)))
                 
                 # Convert percentage values to decimals if they're greater than 1
                 if x_val > 1:
                     x_val = x_val / 100.0
                 if y_val > 1:
                     y_val = y_val / 100.0
                 if w_val > 1:
                     w_val = w_val / 100.0
                 if h_val > 1:
                     h_val = h_val / 100.0
                 
                 # Convert to pixels
                 x = int(width * x_val)
                 y = int(height * y_val)
                 w = int(width * w_val)
                 h = int(height * h_val)
                 
                 self.logger.info(f"Hero card 2 region: x={x}, y={y}, w={w}, h={h} (from {x_val:.4f}, {y_val:.4f}, {w_val:.4f}, {h_val:.4f})")
                 if x >= 0 and y >= 0 and w > 0 and h > 0 and x + w <= width and y + h <= height:
                     card2_img = table_image[y:y+h, x:x+w]
                     if debug:
                         cv2.imwrite("debug_cards/improved/hero_card2.png", card2_img)
                         self.logger.info("Saved hero card 2 debug image")
                 else:
                     self.logger.warning(f"Hero card 2 region out of bounds: x={x}, y={y}, w={w}, h={h}")
             
-            # Process each card with improved result handling
-            def extract_card_code(result):
-                """Extract card code from various result formats"""
-                if result is None:
-                    return None
-                if isinstance(result, tuple) and len(result) >= 1:
-                    return result[0] if result[0] not in ('empty', 'error') else None
-                elif isinstance(result, dict):
-                    card_code = result.get('card_code', 'empty')
-                    return card_code if card_code not in ('empty', 'error') else None
-                return None
-            
-            card1_result = self.recognize_card(card1_img, debug) if card1_img is not None else None
-            card2_result = self.recognize_card(card2_img, debug) if card2_img is not None else None
-            
-            self.logger.info(f"Card 1 result: {card1_result}")
-            self.logger.info(f"Card 2 result: {card2_result}")
-            
-            # Create hole cards object
-            hole_cards = HoleCards()
-            
-            # Extract card codes safely
-            card1_code = extract_card_code(card1_result)
-            card2_code = extract_card_code(card2_result)
-            
-            if card1_code:
-                hole_cards.cards[0] = card1_code
-                self.logger.info(f"Hero card 1 recognized: {card1_code}")
-                
-            if card2_code:
-                hole_cards.cards[1] = card2_code
-                self.logger.info(f"Hero card 2 recognized: {card2_code}")
-                
-            self.logger.info(f"IMPROVED SYSTEM: Final hole cards: {hole_cards}")
-            return hole_cards
+            # Process each card with improved recognition
+            card1_result = None
+            card2_result = None
+            
+            if card1_img is not None and card1_img.size > 0:
+                self.logger.info("Processing hero card 1...")
+                card1_result = self.recognize_card(card1_img, debug)
+                self.logger.info(f"Hero card 1 recognition result: {card1_result}")
+            
+            if card2_img is not None and card2_img.size > 0:
+                self.logger.info("Processing hero card 2...")
+                card2_result = self.recognize_card(card2_img, debug)
+                self.logger.info(f"Hero card 2 recognition result: {card2_result}")
+            
+            # Create hole cards object and populate it
+            hole_cards = HoleCards()
+            
+            # Convert results to Card objects for HoleCards
+            try:
+                from src.card_recognizer import Card
+            except ImportError:
+                try:
+                    from card_recognizer import Card
+                except ImportError:
+                    # Create minimal Card class
+                    class Card:
+                        def __init__(self, rank, suit, confidence=0.0):
+                            self.rank = rank
+                            self.suit = suit
+                            self.confidence = confidence
+                        def __str__(self):
+                            return f"{self.rank} of {{'h': 'Hearts', 'd': 'Diamonds', 'c': 'Clubs', 's': 'Spades'}.get(self.suit, self.suit)}"
+            
+            # Process card 1 result
+            if card1_result and isinstance(card1_result, tuple) and len(card1_result) >= 2:
+                card_code, confidence = card1_result[0], card1_result[1]
+                if card_code and card_code not in ('empty', 'error', 'unknown') and len(card_code) >= 2:
+                    rank, suit = card_code[0], card_code[1]
+                    hole_cards.card1 = Card(rank=rank, suit=suit, confidence=confidence)
+                    self.logger.info(f"Hero card 1 recognized: {hole_cards.card1}")
+            
+            # Process card 2 result
+            if card2_result and isinstance(card2_result, tuple) and len(card2_result) >= 2:
+                card_code, confidence = card2_result[0], card2_result[1]
+                if card_code and card_code not in ('empty', 'error', 'unknown') and len(card_code) >= 2:
+                    rank, suit = card_code[0], card_code[1]
+                    hole_cards.card2 = Card(rank=rank, suit=suit, confidence=confidence)
+                    self.logger.info(f"Hero card 2 recognized: {hole_cards.card2}")
+            
            # 9. Lower the confidence threshold to be more permissive
            if final_confidence < 0.3 and empty_confidence > 0.8:
                self.logger.info(f"Overriding very low confidence card ({card_code}, {final_confidence:.2f}) with empty slot detection")
                return ('empty', empty_confidence, 'low_confidence_override') if return_tuple else self._create_empty_result(empty_confidence)
+                hole_cards.detection_confidence = hole_cards.card1.confidence / 2
+            elif hole_cards.card2:
+                hole_cards.detection_confidence = hole_cards.card2.confidence / 2
+            else:
+                hole_cards.detection_confidence = 0.0
+            
+            hole_cards.timestamp = time.time()
+            
+            self.logger.info(f"IMPROVED SYSTEM: Final hole cards: {hole_cards} (confidence: {hole_cards.detection_confidence:.3f})")
+            return hole_cards
             
         except Exception as e:
             self.logger.error(f"Error in recognize_hero_hole_cards: {e}", exc_info=True)
             return HoleCards()