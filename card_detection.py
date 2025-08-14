"""Card detection and OCR related utilities extracted from SMART_POKER_BOT.

All functions expect a `bot` instance (SmartPokerBot) providing attributes:
  - current_regions (dict)
  - debug (bool)
  - game_state (optional)
  - _detect_rank_focused (method in bot for focused rank OCR)
  - _save_debug_image (method)
  - measure decorator remains on wrapper methods inside bot
  - OCR availability constants / globals (pytesseract, OCR_AVAILABLE)

This module isolates complex logic to shrink SMART_POKER_BOT.py
and allow iterative improvement & unit testing.
"""
from __future__ import annotations
import time
import cv2
import numpy as np
try:
    import pytesseract  # type: ignore
except Exception:  # pragma: no cover
    pytesseract = None  # type: ignore

from collections import deque
from ocr_utils import detect_rank_focused as ocr_detect_rank_focused  # reuse focused rank detection

# ---------------------------------------------------------------------------
# Internal helpers for stabilization & caching
# ---------------------------------------------------------------------------

def _ensure_history(bot):
    if not hasattr(bot, '_card_history'):
        bot._card_history = {}
    if not hasattr(bot, '_ocr_cache'):
        bot._ocr_cache = {}

def _avg_hash(image):
    try:
        g = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        small = cv2.resize(g, (16, 16), interpolation=cv2.INTER_AREA)
        mean = small.mean()
        bits = (small > mean).flatten()
        return ''.join('1' if b else '0' for b in bits)
    except Exception:
        return None

MISREAD_MAP = {
    '0': 'O', 'O': '0', '1': 'I', 'I': '1', 'TO': '10', 'T0': '10', '1O': '10', 'IO': '10'
}
 
# ------------------------- Baseline Rank (Fast Path) ------------------------

def baseline_rank_fast(bot, card_region, debug_name: str):
    """Very fast, high-precision single-rank OCR.

    Strategy (matches the proven static baseline):
      - Crop small top-left area containing rank glyph (≈55% width/height)
      - Grayscale, 3x upscale (cubic), OTSU binarize
      - Tesseract image_to_data (psm 8) with strict rank whitelist (single chars)
      - Pick highest-confidence valid rank character

    Returns single-character rank (2-9,T,J,Q,K,A) or None.
    Safe to call every frame; avoids heavier multi-crop pipelines until needed.
    """
    if pytesseract is None:
        return None
    try:
        if card_region is None or card_region.size == 0:
            return None
        h, w = card_region.shape[:2]
        if h < 8 or w < 8:
            return None
        # Allow disabling via bot flag for experimentation
        if getattr(bot, 'disable_baseline_rank', False):
            return None
        # Focused crop (slightly generous 55% like static tester)
        crop = card_region[0:int(h*0.55), 0:int(w*0.55)]
        if crop.size == 0:
            return None
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop
        up = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        try:
            _, th = cv2.threshold(up, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        except Exception:
            th = up
        config = '--oem 3 --psm 8 -c tessedit_char_whitelist=23456789TJQKA'
        data = pytesseract.image_to_data(th, config=config, output_type=pytesseract.Output.DICT)
        best_char = None
        best_conf = -1
        for txt, conf in zip(data.get('text', []), data.get('conf', [])):
            try:
                ci = int(conf)
            except Exception:
                continue
            t = (txt or '').strip().upper()
            if t in {'2','3','4','5','6','7','8','9','T','J','Q','K','A'} and ci >= 0:
                if ci > best_conf:
                    best_conf = ci
                    best_char = t
        if best_char and getattr(bot, 'debug', False):
            print(f"🅱️ {debug_name}: Baseline rank → {best_char} ({best_conf})")
        return best_char
    except Exception as e:
        if getattr(bot, 'debug', False):
            print(f"⚠️ {debug_name}: Baseline rank error {e}")
        return None

def _normalize_rank_text(text: str):
    t = text.upper()
    for k, v in MISREAD_MAP.items():
        if k in t:
            t = t.replace(k, v)
    # Convert any 10 variants to T (for single char rank representation)
    if '10' in t:
        return 'T'
    # Return first valid rank char if present
    for ch in '23456789TJQKA':
        if ch in t:
            return ch
    return None

def update_card_history(bot, region_name: str, candidate: str | None, presence: bool = True):
    """Track recent detections and return stabilized value or None.

    Rules:
      - Require 2 consecutive identical non-unknown values OR 3 matches in last 4.
      - Allow partial cards (with '?') to be stabilized for UI display.
      - Maintain miss counter; after 2 consecutive misses (presence False or candidate None), clear stable.
    """
    _ensure_history(bot)
    entry = bot._card_history.get(region_name)
    now = time.time()
    if entry is None:
        entry = {'values': deque(maxlen=4), 'stable': None, 'misses': 0, 'last_seen': 0.0}
        bot._card_history[region_name] = entry

    # Allow partial cards to be stabilized (don't filter out '?' cards)
    candidate_clean = candidate

    if candidate_clean:
        entry['values'].append(candidate_clean)
        entry['last_seen'] = now
        entry['misses'] = 0
        vals = list(entry['values'])
        stabilized = False
        if len(vals) >= 2 and vals[-1] == vals[-2]:
            stabilized = True
        elif len(vals) == 4 and vals.count(candidate_clean) >= 3:
            stabilized = True
        if stabilized and candidate_clean not in (None, 'Unknown Card'):
            if entry['stable'] != candidate_clean and getattr(bot, 'debug', False):
                print(f"🧊 Stabilized {region_name}: {candidate_clean} (history={list(entry['values'])})")
            entry['stable'] = candidate_clean
    else:
        # No candidate this cycle
        if not presence:
            entry['misses'] += 1
            if entry['misses'] >= 2:
                if entry['stable'] is not None and bot.debug:
                    print(f"💨 Clearing stable {region_name} after misses")
                entry['stable'] = None
        else:
            # presence but no candidate -> minor miss
            entry['misses'] += 1
    return entry['stable']

# ------------------------- Presence / Color Analysis -------------------------

def detect_card_presence_by_color(bot, card_region, debug_name: str):
    try:
        hsv = cv2.cvtColor(card_region, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(card_region, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray)
        contrast = np.std(gray)
        green_felt_lower = np.array([40, 50, 20])
        green_felt_upper = np.array([80, 255, 255])
        green_mask = cv2.inRange(hsv, green_felt_lower, green_felt_upper)
        green_pixels = cv2.countNonZero(green_mask)
        total_pixels = card_region.shape[0] * card_region.shape[1]
        if total_pixels == 0:
            return False
        green_percentage = (green_pixels / total_pixels) * 100
        bright_pixels = cv2.countNonZero(cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY)[1])
        bright_percentage = (bright_pixels / total_pixels) * 100
        has_high_brightness = brightness > 12
        has_good_contrast = contrast > 15
        has_low_green = green_percentage < 50
        has_bright_areas = bright_percentage > 5
        strong_indicators = sum([
            has_high_brightness and has_good_contrast,
            has_low_green and has_bright_areas,
        ])
        weak_indicators = sum([
            has_high_brightness,
            has_good_contrast,
            has_low_green,
            has_bright_areas,
        ])
        has_card = strong_indicators >= 1 or weak_indicators >= 2
        if bot.debug:
            print(
                f"   🎨 {debug_name}: B={brightness:.1f}, C={contrast:.1f}, "
                f"G={green_percentage:.1f}%, Br={bright_percentage:.1f}% → "
                f"{'CARD' if has_card else 'EMPTY'} (indicators:{weak_indicators}/4)"
            )
        return has_card
    except Exception as e:  # pragma: no cover - defensive
        print(f"❌ Card presence detection error for {debug_name}: {e}")
        return False

# ------------------------- Consistency & Individual Detection ----------------

def detect_card_with_consistency(bot, frame, region_name: str, debug_name: str):
    try:
        attempts = []
        max_attempts = 2
        for attempt in range(max_attempts):
            result = detect_individual_card(bot, frame, region_name, f"{debug_name} (attempt {attempt+1})")
            if result and result != "Unknown Card":
                attempts.append(result)
                if len(result) >= 2 and result[1] in '♠♥♦♣':
                    return result
        if attempts:
            if len(set(attempts)) == 1:
                result = attempts[0]
                print(f"✅ {debug_name}: Consistent result → {result}")
                return result
            ranks = [r[0] for r in attempts if len(r) >= 1]
            suits = [r[-1] for r in attempts if len(r) >= 2 and r[-1] in '♠♥♦♣']
            if ranks and suits:
                most_common_rank = max(set(ranks), key=ranks.count) if ranks else None
                most_common_suit = max(set(suits), key=suits.count) if suits else None
                if most_common_rank and most_common_suit:
                    combined = f"{most_common_rank}{most_common_suit}"
                    print(f"✅ {debug_name}: Combined result → {combined} (from {attempts})")
                    return combined
            complete_results = [r for r in attempts if len(r) >= 2 and r[1] in '♠♥♦♣']
            if complete_results:
                result = complete_results[0]
                print(f"⚠️ {debug_name}: Best attempt → {result}")
                return result
            result = attempts[0]
            print(f"⚠️ {debug_name}: Fallback result → {result}")
            return result
        # If no attempts yielded anything meaningful, perform a single direct detection
        return detect_individual_card(bot, frame, region_name, debug_name)
    except Exception as e:
        print(f"❌ Consistency detection error for {debug_name}: {e}")
        return None

def detect_individual_card(bot, frame, region_name: str, debug_name: str):
    try:
        if region_name not in bot.current_regions:
            return None
        x1, y1, x2, y2 = bot.current_regions[region_name]['region']
        card_region = frame[y1:y2, x1:x2]
        if card_region.size == 0:
            return None
        if getattr(bot, 'debug', False):
            print(f"🔍 Analyzing {debug_name} - Region size: {card_region.shape}")
        # 1. Baseline ultra-fast rank attempt on raw region
        rank = baseline_rank_fast(bot, card_region, debug_name)
        suit = detect_suit_by_color(bot, card_region, debug_name)
        if rank and suit:
            if getattr(bot, 'debug', False):
                print(f"✅ {debug_name}: Baseline Detection → {rank}{suit}")
            return f"{rank}{suit}"
        # 2. Process + upscale for advanced focused OCR only if needed
        processed_region = preprocess_for_cards(bot, card_region, debug_name)
        if min(card_region.shape[0], card_region.shape[1]) < 70:
            processed_region = upscale_for_ocr(bot, processed_region, debug_name)
        if not rank:
            rank = bot._detect_rank_focused(processed_region, debug_name)
        if not suit:
            suit = detect_suit_by_color(bot, card_region, debug_name)
        # Lightweight contour based single‑char rank fallback if focused failed
        if not rank:
            fallback_rank = _rank_ocr_contour_fallback(bot, card_region, debug_name)
            if fallback_rank:
                rank = fallback_rank
        if rank and suit:
            card_result = f"{rank}{suit}"
            if getattr(bot, 'debug', False):
                print(f"✅ {debug_name}: Focused Detection → {card_result}")
            return card_result
        # Try fast OCR first for speed, fallback to enhanced OCR if needed
        try:
            from fast_ocr import fast_card_ocr
            card_value = fast_card_ocr(bot, processed_region, debug_name)
            if card_value:
                return card_value
        except ImportError:
            pass
        
        card_value = enhanced_card_ocr(bot, processed_region, debug_name)
        if card_value:
            return card_value
        if rank:
            if getattr(bot, 'debug', False):
                print(f"⚠️ {debug_name}: Only rank detected → {rank}?")
            return f"{rank}?"
        if suit:
            # Try the fallback OCR for rank when we only have suit
            fallback_rank = _rank_ocr_contour_fallback(bot, card_region, debug_name)
            if fallback_rank:
                if getattr(bot, 'debug', False):
                    print(f"🎯 {debug_name}: Fallback rank found → {fallback_rank}{suit}")
                return f"{fallback_rank}{suit}"
            else:
                if getattr(bot, 'debug', False):
                    print(f"⚠️ {debug_name}: Only suit detected → ?{suit}")
                # Save debug image to inspect rank region when only suit is found
                try:
                    if hasattr(bot, '_save_debug_image'):
                        bot._save_debug_image(card_region, f"only_suit_{debug_name}")
                except Exception:
                    pass
                return f"?{suit}"
        if has_card_pattern(bot, card_region):
            if getattr(bot, 'debug', False):
                print(f"⚠️ {debug_name}: Card pattern detected but couldn't read value")
            bot._save_debug_image(card_region, debug_name)
            return "Unknown Card"
        if getattr(bot, 'debug', False):
            print(f"❌ {debug_name}: No card detected")
        return None
    except Exception as e:
        print(f"❌ Error detecting {debug_name}: {e}")
        return None

# ------------------------- Preprocessing & Upscaling -------------------------

def preprocess_for_cards(bot, card_region, debug_name: str):
    try:
        if card_region.size == 0:
            return card_region
        if len(card_region.shape) == 3:
            gray = cv2.cvtColor(card_region, cv2.COLOR_BGR2GRAY)
        else:
            gray = card_region
        processed_versions = []
        enhanced = cv2.convertScaleAbs(gray, alpha=2.5, beta=10)
        denoised = cv2.bilateralFilter(enhanced, 9, 75, 75)
        processed_versions.append(("enhanced_denoised", denoised))
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        morph_enhanced = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
        morph_enhanced = cv2.convertScaleAbs(morph_enhanced, alpha=2.0, beta=5)
        processed_versions.append(("morphological", morph_enhanced))
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        sharpened = cv2.addWeighted(gray, 2.5, blurred, -1.5, 0)
        sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)
        processed_versions.append(("sharpened", sharpened))
        adaptive = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(4,4))
        clahe_enhanced = adaptive.apply(gray)
        processed_versions.append(("adaptive", clahe_enhanced))
        best_version = select_best_preprocessing(bot, processed_versions, debug_name)
        if len(best_version.shape) == 2:
            best_version = cv2.cvtColor(best_version, cv2.COLOR_GRAY2BGR)
        return best_version
    except Exception as e:
        print(f"❌ Enhanced preprocessing error for {debug_name}: {e}")
        return card_region

# ------------------------- Extra Rank Fallback ------------------------------

def _rank_ocr_contour_fallback(bot, card_region, debug_name: str):
    """Very small single character OCR fallback using contour isolation.

    Tries to extract the brightest plausible rank glyph and run a tiny set of
    Tesseract configurations optimized for one character. Returns a normalized
    rank char or None.
    """
    if card_region is None or card_region.size == 0 or pytesseract is None:
        return None
    try:
        h, w = card_region.shape[:2]
        tl = card_region[0:max(h//2, 1), 0:max(w//2, 1)]
        gray = cv2.cvtColor(tl, cv2.COLOR_BGR2GRAY)
        norm = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
        enhanced = cv2.convertScaleAbs(norm, alpha=2.8, beta=10)
        variants = []
        # OTSU
        try:
            variants.append(cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1])
        except Exception:
            pass
        # Adaptive
        for method in [(cv2.ADAPTIVE_THRESH_MEAN_C, "mean"), (cv2.ADAPTIVE_THRESH_GAUSSIAN_C, "gauss")]:
            try:
                variants.append(cv2.adaptiveThreshold(enhanced, 255, method[0], cv2.THRESH_BINARY, 11, 4))
            except Exception:
                pass
        # Invert copies
        variants.extend([cv2.bitwise_not(v) for v in list(variants)])
        whitelist = '23456789TJQKA10'
        configs = [
            '--oem 3 --psm 10 -c tessedit_char_whitelist=' + whitelist,
            '--oem 3 --psm 13 -c tessedit_char_whitelist=' + whitelist,
            '--oem 3 --psm 8 -c tessedit_char_whitelist=' + whitelist,
        ]
        best_text = None
        for v in variants:
            try:
                cnts, _ = cv2.findContours(v, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if not cnts:
                    continue
                cnt = max(cnts, key=cv2.contourArea)
                x, y, cw, ch = cv2.boundingRect(cnt)
                if cw * ch < 30:
                    continue
                crop = v[y:y+ch, x:x+cw]
                crop = cv2.copyMakeBorder(crop, 2, 2, 2, 2, cv2.BORDER_CONSTANT, value=0)
            except Exception:
                crop = v
            for cfg in configs:
                try:
                    txt = pytesseract.image_to_string(crop, config=cfg).strip().upper()
                except Exception:
                    continue
                if not txt:
                    continue
                txt = txt.replace('10', 'T')
                for ch in txt:
                    if ch in '23456789TJQKA':
                        best_text = ch
                        break
                if best_text:
                    break
            if best_text:
                break
        if best_text and getattr(bot, 'debug', False):
            print(f"🔢 {debug_name}: Contour fallback rank → {best_text}")
        return best_text
    except Exception:
        return None

def upscale_for_ocr(bot, img, debug_name: str):
    try:
        work = img.copy()
        if len(work.shape) == 2:
            work = cv2.cvtColor(work, cv2.COLOR_GRAY2BGR)
        h, w = work.shape[:2]
        iters = 0
        while min(h, w) < 120 and iters < 3:
            work = cv2.resize(work, (w*2, h*2), interpolation=cv2.INTER_CUBIC)
            h, w = work.shape[:2]
            iters += 1
        work = cv2.bilateralFilter(work, 7, 60, 60)
        blur = cv2.GaussianBlur(work, (0,0), 1.0)
        work = cv2.addWeighted(work, 1.8, blur, -0.8, 0)
        work = cv2.convertScaleAbs(work, alpha=1.25, beta=5)
        return work
    except Exception as e:
        if bot.debug:
            print(f"⚠️ Upscale failed for {debug_name}: {e}")
        return img

def select_best_preprocessing(bot, processed_versions, debug_name: str):
    try:
        best_score = 0
        best_image = processed_versions[0][1]
        for name, image in processed_versions:
            contrast_score = cv2.Laplacian(image, cv2.CV_64F).var()
            edges = cv2.Canny(image, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            combined_score = contrast_score + (edge_density * 1000)
            if combined_score > best_score:
                best_score = combined_score
                best_image = image
        return best_image
    except Exception:
        return processed_versions[0][1]

# ------------------------- OCR Enhancements -------------------------

def enhanced_card_ocr(bot, card_region, debug_name: str = "card"):
    try:
        if card_region is None or card_region.size == 0:
            return None
        h, w = card_region.shape[:2]
        rank_region = card_region[0:int(h*0.4), 0:w]
        if rank_region.size == 0:
            return None
        if len(rank_region.shape) == 3:
            gray = cv2.cvtColor(rank_region, cv2.COLOR_BGR2GRAY)
        else:
            gray = rank_region
        approaches = [
            ("Original", gray),
            ("Contrast", cv2.convertScaleAbs(gray, alpha=2.0, beta=-50)),
            ("Gaussian", cv2.GaussianBlur(gray, (3, 3), 0)),
            ("Bilateral", cv2.bilateralFilter(gray, 9, 75, 75)),
            ("CLAHE", cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8)).apply(gray)),
            ("Threshold", cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]),
            ("Adaptive", cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)),
        ]
        best_result = None
        best_confidence = 0
        for approach_name, processed in approaches:
            if pytesseract is None:
                continue
            try:
                # Cache by hash+approach to avoid repeated OCR on identical subimages
                img_hash = _avg_hash(processed)
                cache_key = (img_hash, approach_name)
                config = '--oem 3 --psm 8 -c tessedit_char_whitelist=23456789TJQKA10'
                if img_hash and cache_key in getattr(bot, '_ocr_cache', {}):
                    cached = bot._ocr_cache[cache_key]
                    if cached:
                        return cached
                data = pytesseract.image_to_data(processed, config=config, output_type=pytesseract.Output.DICT)
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                text = pytesseract.image_to_string(processed, config=config).strip().upper()
                if text and avg_confidence > max(best_confidence, 40):
                    cleaned = ''.join(c for c in text if c.isalnum())
                    norm = _normalize_rank_text(cleaned)
                    if norm:
                        best_result = norm
                        best_confidence = avg_confidence
                        if img_hash:
                            _ensure_history(bot)
                            bot._ocr_cache[cache_key] = norm
            except Exception:
                continue
        return best_result
    except Exception as e:
        print(f"❌ Enhanced OCR error for {debug_name}: {e}")
        return None

# ------------------------- Suit & Rank Detection -----------------------------

def detect_suit_by_color(bot, card_region, debug_name: str):
    try:
        hsv = cv2.cvtColor(card_region, cv2.COLOR_BGR2HSV)
        color_ranges = {
            '♠': [(0, 0, 0), (180, 255, 100)],
            '♥': [(0, 120, 70), (10, 255, 255)],
            '♦': [(100, 120, 70), (130, 255, 255)],
            '♣': [(40, 120, 70), (80, 255, 255)],
        }
        red_upper = [(170, 120, 70), (180, 255, 255)]
        suit_scores = {}
        for suit, (lower, upper) in color_ranges.items():
            lower_bound = np.array(lower)
            upper_bound = np.array(upper)
            mask = cv2.inRange(hsv, lower_bound, upper_bound)
            if suit == '♥':
                lower_bound2 = np.array(red_upper[0])
                upper_bound2 = np.array(red_upper[1])
                mask2 = cv2.inRange(hsv, lower_bound2, upper_bound2)
                mask = cv2.bitwise_or(mask, mask2)
            pixel_count = cv2.countNonZero(mask)
            total_pixels = card_region.shape[0] * card_region.shape[1]
            percentage = (pixel_count / total_pixels) * 100 if total_pixels else 0
            suit_scores[suit] = percentage
            if bot.debug:
                print(f"🎨 {debug_name} - {suit}: {percentage:.1f}% pixels")
        best_suit = max(suit_scores, key=suit_scores.get)
        if suit_scores[best_suit] >= 1.0:
            if bot.debug:
                print(f"🎨 {debug_name}: Color detected → {best_suit} ({suit_scores[best_suit]:.1f}%)")
            return best_suit
        if bot.debug:
            print(f"🎨 {debug_name}: No clear color detected, defaulting to ♠")
        return '♠'
    except Exception as e:
        print(f"❌ Color detection error for {debug_name}: {e}")
        return '♠'

def detect_rank_ocr(bot, card_region, debug_name: str):
    try:
        if pytesseract is None:
            return None
        approaches = [
            {'region': (0, 0, min(card_region.shape[1]//2, 50), min(card_region.shape[0]//2, 50)), 'alpha':2.5,'beta':0,'description':'upper-left corner'},
            {'region': (0, 0, card_region.shape[1], card_region.shape[0]//3), 'alpha':2.0,'beta':10,'description':'upper third'},
            {'region': (0, 0, card_region.shape[1]//2, card_region.shape[0]), 'alpha':1.8,'beta':5,'description':'left half'},
            {'region': (0, 0, card_region.shape[1], card_region.shape[0]), 'alpha':1.5,'beta':0,'description':'whole card'},
        ]
        for i, approach in enumerate(approaches):
            y1, x1, x2, y2 = approach['region']
            rank_region = card_region[y1:y2, x1:x2]
            if rank_region.size == 0:
                continue
            gray = cv2.cvtColor(rank_region, cv2.COLOR_BGR2GRAY)
            preprocessed_images = [
                cv2.convertScaleAbs(gray, alpha=approach['alpha'], beta=approach['beta']),
                cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
                cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2),
                cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1],
            ]
            for j, processed in enumerate(preprocessed_images):
                try:
                    configs = [
                        '--oem 3 --psm 8 -c tessedit_char_whitelist=23456789TJQKA10',
                        '--oem 3 --psm 7 -c tessedit_char_whitelist=23456789TJQKA10',
                        '--oem 3 --psm 6 -c tessedit_char_whitelist=23456789TJQKA10',
                    ]
                    for config in configs:
                        text = pytesseract.image_to_string(processed, config=config).strip().upper()
                        text = ''.join(c for c in text if c.isalnum())
                        valid_ranks = ['2','3','4','5','6','7','8','9','T','J','Q','K','A','10']
                        if '10' in text:
                            print(f"🔢 {debug_name}: Rank detected → 10 (approach {i+1}: {approach['description']}, preprocess {j+1})")
                            return '10'
                        for rank in valid_ranks:
                            if rank in text and rank != '10':
                                print(f"🔢 {debug_name}: Rank detected → {rank} (approach {i+1}: {approach['description']}, preprocess {j+1})")
                                print(f"🔢 Raw OCR text: '{text}'")
                                return rank
                except Exception:
                    continue
        print(f"⚠️ {debug_name}: Could not detect rank with any approach")
        return None
    except Exception as e:
        print(f"❌ Rank detection error for {debug_name}: {e}")
        return None

# ------------------------- Pattern Detection ---------------------------------

def has_card_pattern(bot, card_region):
    try:
        gray = cv2.cvtColor(card_region, cv2.COLOR_BGR2GRAY)
        contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 200:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h if h > 0 else 0
                if 0.3 < aspect_ratio < 2.0 and area > 500:
                    return True
        return False
    except Exception:
        return False

# ------------------------- Public Facade Functions ---------------------------

def detect_hero_cards(bot, frame):
    try:
        detected_cards = []
        _ensure_history(bot)
        for i in range(1, 3):
            region_name = f'hero_card_{i}'
            stable_before = bot._card_history.get(region_name, {}).get('stable') if hasattr(bot, '_card_history') else None
            presence = False
            candidate = None
            if region_name in bot.current_regions:
                try:
                    x1, y1, x2, y2 = bot.current_regions[region_name]['region']
                    region_img = frame[y1:y2, x1:x2]
                    if region_img.size == 0:
                        presence = False
                    else:
                        presence = detect_card_presence_by_color(bot, region_img, f"Hero Presence {i}")
                        if presence:
                            candidate = detect_card_with_consistency(bot, frame, region_name, f"Hero Card {i}")
                except Exception:
                    pass
            stable_val = update_card_history(bot, region_name, candidate, presence)
            final_val = stable_val if stable_val else stable_before
            if bot.debug:
                print(f"🔍 DEBUG: {region_name} - candidate: {candidate}, stable_val: {stable_val}, final_val: {final_val}")
            if final_val:
                detected_cards.append(final_val)
        if bot.debug:
            print(f"🔍 HERO stabilized: {detected_cards}")
        return detected_cards[:2]
    except Exception as e:
        print(f"❌ Error detecting hero cards: {e}")
        return []

__all__ = [
    'detect_hero_cards', 'detect_card_with_consistency', 'detect_individual_card',
    'preprocess_for_cards', 'upscale_for_ocr', 'enhanced_card_ocr', 'detect_suit_by_color',
    'detect_card_presence_by_color', 'has_card_pattern', 'update_card_history', 'detect_rank_ocr'
]
