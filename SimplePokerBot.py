#!/usr/bin/env python3
"""Simple Poker Bot - On-Demand OCR Analysis Only.

Stripped down version that only does single-frame capture and OCR analysis.
No live feed, no continuous processing, no threading.
Enhanced with tournament stack tracking capabilities and poker engine integration.
"""
import os
import json
import cv2
import numpy as np
import time
import re
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

# Import poker engine for advanced analysis
try:
    from poker_engine import PokerEngine
    POKER_ENGINE_AVAILABLE = True
except ImportError:
    POKER_ENGINE_AVAILABLE = False

try:
    from opponent_card_detector import OpponentCardDetector
    OPPONENT_DETECTOR_AVAILABLE = True
except ImportError:
    OPPONENT_DETECTOR_AVAILABLE = False
    print("⚠️ Poker Engine not available - basic OCR only")

class PokerStage(Enum):
    """Poker game stages"""
    PRE_FLOP = "Pre-Flop"
    FLOP = "Flop" 
    TURN = "Turn"
    RIVER = "River"
    UNKNOWN = "Unknown"

class Position(Enum):
    """Player positions relative to hero (bottom center)."""
    HERO = "Hero"
    POSITION_1 = "Position_1"  # Left of hero
    POSITION_2 = "Position_2"  # Top left
    POSITION_3 = "Position_3"  # Top center left
    POSITION_4 = "Position_4"  # Top center
    POSITION_5 = "Position_5"  # Top center right
    POSITION_6 = "Position_6"  # Top right
    POSITION_7 = "Position_7"  # Right of hero
    POSITION_8 = "Position_8"  # Bottom right

@dataclass
class PlayerStack:
    """Player stack information."""
    name: str
    chips: Optional[int] = None
    bb_size: Optional[float] = None
    position: Optional[Position] = None
    last_updated: Optional[float] = None
    confidence: float = 0.0

@dataclass
class TournamentState:
    """Complete tournament state."""
    players: Dict[Position, PlayerStack]
    total_chips: int
    current_bb: int
    current_sb: int
    hero_position: Position = Position.HERO
    tournament_start_time: Optional[float] = None
    last_update: Optional[float] = None

class SimplePokerBot:
    """Simple poker bot for on-demand OCR analysis with tournament tracking."""
    
    def __init__(self):
        """Initialize bot with region loading, tournament tracking, and poker engine."""
        self.current_regions = {}
        self.load_regions()
        
        # Stage detection
        self.stage_card_counts = {
            PokerStage.PRE_FLOP: 0,
            PokerStage.FLOP: 3,
            PokerStage.TURN: 4,
            PokerStage.RIVER: 5
        }
        
        # Track hand progression
        self.previous_stage = PokerStage.UNKNOWN
        self.current_stage = PokerStage.UNKNOWN
        self.hand_count = 0
        self.hand_finish_reason = "Unknown"
        
        # Tournament tracking
        self.tournament_enabled = True
        self.tournament_state = TournamentState(
            players={},
            total_chips=0,
            current_bb=1,
            current_sb=1
        )
        
        # Stack tracking regions
        self.stack_regions = {}
        self.name_regions = {}
        
        # Initialize player positions
        self._initialize_tournament_positions()
        
        # Tournament settings
        self.starting_chips = 1500  # Typical SNG starting chips
        self.max_players = 9
        
        # Initialize poker engine
        if POKER_ENGINE_AVAILABLE:
            self.poker_engine = PokerEngine()
            print("✅ Poker Engine initialized - Advanced analysis enabled")
        else:
            self.poker_engine = None
            print("⚠️ Poker Engine disabled - Basic OCR only")
        
        # Initialize opponent card detector
        if OPPONENT_DETECTOR_AVAILABLE:
            self.opponent_detector = OpponentCardDetector()
            self.opponent_card_regions = {}  # Will be generated from name regions
            print("✅ Opponent card detector initialized - Player tracking enabled")
        else:
            self.opponent_detector = None
            print("⚠️ Opponent card detector disabled - Basic player estimation only")
        
        # Load stack regions if available
        self.load_stack_regions()
        
        # Generate opponent card detection regions when name regions are loaded
        if self.opponent_detector and hasattr(self, 'name_regions') and self.name_regions:
            self.opponent_card_regions = self.opponent_detector.generate_card_regions(self.name_regions)
            print(f"🃏 Generated {len(self.opponent_card_regions)} opponent card detection regions")
        
        print("🏆 SimplePokerBot initialized with tournament tracking")
        
    def _initialize_tournament_positions(self):
        """Initialize empty tournament player positions."""
        for position in Position:
            self.tournament_state.players[position] = PlayerStack(
                name="Empty",
                position=position
            )
        
    def load_regions(self):
        """Load regions from available JSON files."""
        region_files = [
            'corrected_regions.json',
            'calibrated_regions.json',
            'adjusted_regions.json',
            'community_card_adjustments.json'
        ]
        
        for filename in region_files:
            if os.path.exists(filename):
                try:
                    with open(filename, 'r') as f:
                        data = json.load(f)
                        
                        # Extract regions from different formats
                        if 'regions' in data:
                            self.current_regions = data['regions']
                        elif isinstance(data, dict) and any('card' in k or 'pot' in k for k in data.keys()):
                            self.current_regions = data
                        else:
                            print(f"⚠️ Unknown format in {filename}")
                            continue
                            
                        print(f"✅ Loaded regions from {filename}")
                        print(f"📍 Loaded {len(self.current_regions)} regions: {list(self.current_regions.keys())}")
                        return
                except Exception as e:
                    print(f"⚠️ Failed to load {filename}: {e}")
        
        print("⚠️ No regions loaded - using default regions")
        self.create_default_regions()
    
    def create_default_regions(self):
        """Create basic default regions for 1920x1080 resolution."""
        self.current_regions = {
            'hero_card_1': [960, 850, 80, 120],
            'hero_card_2': [1050, 850, 80, 120],
            'community_card_1': [760, 400, 80, 120],
            'community_card_2': [850, 400, 80, 120],
            'community_card_3': [940, 400, 80, 120],
            'community_card_4': [1030, 400, 80, 120],
            'community_card_5': [1120, 400, 80, 120],
            'pot_amount': [900, 350, 120, 40]
        }
        print("📍 Created default regions")
    
    def load_stack_regions(self, regions_file='stack_regions.json'):
        """Load predefined stack tracking regions for tournament play."""
        try:
            with open(regions_file, 'r') as f:
                regions_data = json.load(f)
                self.stack_regions = regions_data.get('stack_regions', {})
                self.name_regions = regions_data.get('name_regions', {})
                print(f"✅ Loaded {len(self.stack_regions)} stack regions for tournament tracking")
                return True
        except FileNotFoundError:
            print(f"⚠️ {regions_file} not found - tournament stack tracking disabled")
            self.tournament_enabled = False
            return False
        except Exception as e:
            print(f"❌ Error loading stack regions: {e}")
            self.tournament_enabled = False
            return False
    
    def extract_region(self, frame, region_name, from_stack_regions=False):
        """Extract a specific region from the frame (enhanced for stack regions)."""
        if from_stack_regions:
            # Extract from stack/name regions
            regions_dict = {**self.stack_regions, **self.name_regions}
            if region_name not in regions_dict:
                return None
            coords = regions_dict[region_name]
        else:
            # Extract from card regions (original method)
            if region_name not in self.current_regions:
                return None
            coords = self.current_regions[region_name]
        
        if len(coords) != 4:
            return None
            
        x, y, w, h = coords
        height, width = frame.shape[:2]
        
        # Ensure coordinates are within frame bounds
        x = max(0, min(x, width - 1))
        y = max(0, min(y, height - 1))
        w = max(1, min(w, width - x))
        h = max(1, min(h, height - y))
        
        return frame[y:y+h, x:x+w]
    
    def analyze_frame_ocr(self, frame, include_tournament=True, fast_mode=False):
        """Analyze a single frame with OCR, stage detection, and optional tournament tracking.
        
        Args:
            frame: The frame to analyze
            include_tournament: Whether to include tournament analysis (slower)
            fast_mode: If True, only analyze cards and pot for immediate decisions
        """
        if frame is None:
            return {'error': 'No frame provided'}
        
        start_time = time.time()
        print(f"🔍 Analyzing frame: {frame.shape[1]}x{frame.shape[0]} {'(FAST MODE)' if fast_mode else ''}")
        print(f"📍 Available regions: {list(self.current_regions.keys())}")
        
        # PHASE 1: CRITICAL ANALYSIS (Cards + Pot) - Always fast
        phase1_start = time.time()
        
        # Detect community cards and determine stage
        community_cards = self.analyze_community_cards(frame)
        stage_info = self.detect_current_stage(community_cards)
        
        # Check for hand transitions
        self.check_hand_transition(stage_info['stage'])
        
        # Analyze hero cards
        hero_cards = self.analyze_hero_cards(frame)
        
        # Analyze pot
        pot_value = self.analyze_pot(frame)
        
        phase1_time = (time.time() - phase1_start) * 1000
        
        # PHASE 2: TOURNAMENT ANALYSIS (Optional/Background)
        tournament_results = None
        tournament_metrics = None
        opponent_card_analysis = None
        phase2_time = 0
        
        if not fast_mode and include_tournament and self.tournament_enabled and self.stack_regions:
            phase2_start = time.time()
            tournament_results = self.analyze_tournament_stacks(frame)
            tournament_metrics = self.calculate_tournament_metrics()
            
            # Add opponent card detection for accurate player counting
            opponent_card_analysis = self.analyze_opponent_cards(frame)
            
            phase2_time = (time.time() - phase2_start) * 1000
        
        total_analysis_time = (time.time() - start_time) * 1000
        
        # Print results based on mode
        if fast_mode:
            self.print_fast_analysis_results(hero_cards, community_cards, pot_value, stage_info, phase1_time)
        else:
            self.print_analysis_results(hero_cards, community_cards, pot_value, stage_info, 
                                      tournament_results, tournament_metrics, total_analysis_time, 
                                      phase1_time, phase2_time)
        
        # Return structured results
        ocr_results = {
            'hero_cards': [hero_cards.get(f'hero_card_{i}') for i in range(1, 3)],
            'community_cards': [community_cards.get(f'community_card_{i}') for i in range(1, 6)],
            'pot': pot_value,
            'stage': stage_info['stage'].value,
            'hand_count': self.hand_count,
            'stage_confidence': stage_info['confidence'],
            'hand_finish_reason': self.hand_finish_reason,
            'analysis_time_ms': total_analysis_time,
            'phase1_time_ms': phase1_time,
            'phase2_time_ms': phase2_time,
            'fast_mode': fast_mode
        }
        
        # Add tournament data if available
        if tournament_results:
            ocr_results['tournament'] = {
                'stacks': tournament_results,
                'metrics': tournament_metrics
            }
            
            # Add individual player data for poker engine analysis
            tournament_data = {}
            if hasattr(self, 'stack_regions'):
                for region_name in self.stack_regions.keys():
                    if region_name in tournament_results:
                        tournament_data[region_name] = tournament_results[region_name]
            if hasattr(self, 'name_regions'):
                for region_name in self.name_regions.keys():
                    if region_name in tournament_results:
                        tournament_data[region_name] = tournament_results[region_name]
            
            ocr_results['tournament_data'] = tournament_data
        
        # Add opponent card detection data if available
        if opponent_card_analysis:
            ocr_results['opponent_cards'] = opponent_card_analysis
        
        # POKER ENGINE ANALYSIS - Enhanced intelligence layer
        if self.poker_engine and not fast_mode:
            try:
                # Process through poker engine for advanced analysis
                enhanced_analysis = self.poker_engine.process_ocr_data(ocr_results)
                
                # Print poker engine results
                self.print_poker_engine_results(enhanced_analysis)
                
                # Return enhanced analysis with poker intelligence
                return enhanced_analysis
            except Exception as e:
                print(f"⚠️ Poker engine error: {e}")
                # Fall back to basic OCR results
                return ocr_results
        
        return ocr_results
    
    def analyze_frame_fast(self, frame):
        """Fast analysis for immediate decision making - cards and pot only."""
        return self.analyze_frame_ocr(frame, include_tournament=False, fast_mode=True)
    
    def analyze_frame_tournament(self, frame):
        """Full analysis including tournament tracking - slower but comprehensive."""
        return self.analyze_frame_ocr(frame, include_tournament=True, fast_mode=False)
    
    def analyze_community_cards(self, frame):
        """Analyze all community card regions."""
        community_cards = {}
        
        for i in range(1, 6):  # community_card_1 to community_card_5
            region_name = f'community_card_{i}'
            region = self.extract_region(frame, region_name)
            
            if region is not None:
                print(f"✅ Extracted {region_name}: {region.shape}")
                card_value = self.ocr_card_region(region, region_name)
                community_cards[region_name] = card_value
                
                if card_value:
                    print(f"� {region_name}: {card_value}")
                    
        return community_cards
    
    def analyze_hero_cards(self, frame):
        """Analyze hero card regions with learning system integration."""
        hero_cards = {}
        
        for i in range(1, 3):  # hero_card_1 and hero_card_2
            region_name = f'hero_card_{i}'
            region = self.extract_region(frame, region_name)
            
            if region is not None:
                print(f"✅ Extracted {region_name}: {region.shape}")
                card_value = self.ocr_card_region(region, region_name)
                hero_cards[region_name] = card_value
                
                if card_value:
                    print(f"🃏 {region_name}: {card_value}")
                    
        return hero_cards
    
    def analyze_pot(self, frame):
        """Analyze pot region."""
        pot_region = self.extract_region(frame, 'pot_size')
        if pot_region is None:
            pot_region = self.extract_region(frame, 'pot_amount')
        
        if pot_region is not None:
            print(f"✅ Extracted pot region: {pot_region.shape}")
            pot_text = self.ocr_text_region(pot_region)
            
            if pot_text:
                print(f"💰 Pot: {pot_text}")
                return pot_text
        else:
            print("❌ Failed to extract pot region")
            
        return None
    
    def analyze_tournament_stacks(self, frame):
        """Analyze all player stacks for tournament tracking."""
        if not self.tournament_enabled or not self.stack_regions:
            return {}
        
        player_data = {}
        
        # Analyze each player position
        for position in Position:
            position_name = position.value
            
            # Get stack and name regions
            stack_key = f"{position_name}_stack"
            name_key = f"{position_name}_name"
            
            stack_region = self.stack_regions.get(stack_key)
            name_region = self.name_regions.get(name_key)
            
            # Extract and analyze regions
            stack_text = None
            name_text = None
            
            if stack_region:
                stack_img = self.extract_region(frame, stack_key, from_stack_regions=True)
                if stack_img is not None:
                    stack_text = self.ocr_stack_region(stack_img)
            
            if name_region:
                name_img = self.extract_region(frame, name_key, from_stack_regions=True)
                if name_img is not None:
                    name_text = self.ocr_name_region(name_img)
            
            # Parse player data if we have either stack or name
            if stack_text or name_text:
                player_data[position] = self._parse_player_data(name_text, stack_text, position)
        
        # Update tournament state
        self.update_tournament_state(player_data)
        
        return player_data
    
    def analyze_opponent_cards(self, frame):
        """Analyze which opponents have cards in hand by detecting wine-red card backs."""
        if not self.opponent_detector or not self.opponent_card_regions:
            return None
        
        try:
            # Generate card regions if not already done
            if not self.opponent_card_regions and hasattr(self, 'name_regions') and self.name_regions:
                self.opponent_card_regions = self.opponent_detector.generate_card_regions(self.name_regions)
                print(f"🃏 Generated {len(self.opponent_card_regions)} opponent card detection regions")
            
            if not self.opponent_card_regions:
                return None
            
            # Detect cards in each region
            detection_results = self.opponent_detector.detect_wine_red_cards(frame, self.opponent_card_regions)
            
            # Get active player count
            active_opponents = self.opponent_detector.get_active_opponents(detection_results)
            total_active_players = self.opponent_detector.count_active_players(detection_results, include_hero=True)
            
            return {
                'detection_results': detection_results,
                'active_opponents': active_opponents,
                'active_opponent_count': len(active_opponents),
                'total_active_players': total_active_players,
                'card_regions': self.opponent_card_regions
            }
            
        except Exception as e:
            print(f"❌ Opponent card detection error: {e}")
            return None
    
    def detect_current_stage(self, community_cards):
        """Detect current poker stage based on community cards."""
        # Count detected community cards in correct order
        ordered_regions = ['community_card_1', 'community_card_2', 'community_card_3', 'community_card_4', 'community_card_5']
        detected_cards = [community_cards[region] for region in ordered_regions if region in community_cards and community_cards[region] is not None]
        card_count = len(detected_cards)
        
        # Determine stage
        if card_count == 0:
            stage = PokerStage.PRE_FLOP
        elif card_count == 3:
            stage = PokerStage.FLOP
        elif card_count == 4:
            stage = PokerStage.TURN
        elif card_count == 5:
            stage = PokerStage.RIVER
        else:
            stage = PokerStage.UNKNOWN
        
        # Calculate confidence based on expected vs actual
        expected_count = self.stage_card_counts.get(stage, 0)
        confidence = 1.0 if card_count == expected_count else max(0.0, 1.0 - abs(card_count - expected_count) / 5.0)
        
        return {
            'stage': stage,
            'card_count': card_count,
            'detected_cards': detected_cards,
            'confidence': confidence,
            'expected_count': expected_count
        }
    
    def check_hand_transition(self, new_stage):
        """Check for hand transitions and update counters."""
        if self.current_stage != new_stage:
            self.previous_stage = self.current_stage
            self.current_stage = new_stage
            
            # Detect early hand finish (any stage going back to Pre-Flop)
            if (self.previous_stage in [PokerStage.FLOP, PokerStage.TURN, PokerStage.RIVER] and 
                new_stage == PokerStage.PRE_FLOP):
                self.hand_count += 1
                if self.previous_stage == PokerStage.FLOP:
                    self.hand_finish_reason = "Early Finish (Flop)"
                    print(f"🏁 HAND FINISHED EARLY! Flop → Pre-Flop (Hand #{self.hand_count})")
                elif self.previous_stage == PokerStage.TURN:
                    self.hand_finish_reason = "Early Finish (Turn)"
                    print(f"🏁 HAND FINISHED EARLY! Turn → Pre-Flop (Hand #{self.hand_count})")
                elif self.previous_stage == PokerStage.RIVER:
                    self.hand_finish_reason = "Completed (River)"
                    print(f"🏁 HAND FINISHED! River → Pre-Flop (Hand #{self.hand_count})")
            
            # Detect new hand from unknown state
            elif (self.previous_stage == PokerStage.UNKNOWN and new_stage == PokerStage.PRE_FLOP):
                self.hand_count += 1
                print(f"🆕 NEW HAND DETECTED! Hand #{self.hand_count}")
            
            # Detect normal hand progression
            elif (self.previous_stage == PokerStage.PRE_FLOP and new_stage == PokerStage.FLOP):
                print("📈 HAND PROGRESSION: Pre-Flop → Flop")
            elif (self.previous_stage == PokerStage.FLOP and new_stage == PokerStage.TURN):
                print("📈 HAND PROGRESSION: Flop → Turn")
            elif (self.previous_stage == PokerStage.TURN and new_stage == PokerStage.RIVER):
                print("📈 HAND PROGRESSION: Turn → River")
            
            # Detect unusual backwards transitions (shouldn't happen but good to log)
            elif self._is_backward_transition(self.previous_stage, new_stage):
                stage_order = {PokerStage.PRE_FLOP: 0, PokerStage.FLOP: 1, PokerStage.TURN: 2, PokerStage.RIVER: 3}
                prev_order = stage_order.get(self.previous_stage, -1)
                new_order = stage_order.get(new_stage, -1)
                if prev_order > new_order and new_stage != PokerStage.PRE_FLOP:
                    print(f"⚠️ UNUSUAL TRANSITION: {self.previous_stage.value} → {new_stage.value}")
    
    def _is_backward_transition(self, prev_stage, new_stage):
        """Check if this is a backward transition within the same hand."""
        stage_order = {PokerStage.PRE_FLOP: 0, PokerStage.FLOP: 1, PokerStage.TURN: 2, PokerStage.RIVER: 3}
        prev_order = stage_order.get(prev_stage, -1)
        new_order = stage_order.get(new_stage, -1)
        
        # Backward transition is when we go from a higher stage to a lower stage
        # but NOT when going to Pre-Flop (that's a new hand)
        return (prev_order > new_order and new_order >= 0 and 
                new_stage != PokerStage.PRE_FLOP and prev_stage != PokerStage.UNKNOWN)
    
    def print_analysis_results(self, hero_cards, community_cards, pot_value, stage_info, tournament_results=None, tournament_metrics=None, total_time=None, phase1_time=None, phase2_time=None):
        """Print comprehensive analysis results including tournament data."""
        print("\n" + "="*80)
        print(f"🎮 POKER ANALYSIS - Hand #{self.hand_count}")
        if total_time:
            print(f"⚡ Total Time: {total_time:.1f}ms")
            if phase1_time and phase2_time:
                print(f"📊 Phase 1 (Cards): {phase1_time:.1f}ms | Phase 2 (Tournament): {phase2_time:.1f}ms")
        print("="*80)
        
        # Stage information
        stage = stage_info['stage']
        print(f"🎯 Current Stage: {stage.value}")
        print(f"📊 Community Cards: {stage_info['card_count']}/5 detected")
        print(f"🎪 Confidence: {stage_info['confidence']:.1%}")
        
        # Hero cards
        hero_count = len([card for card in hero_cards.values() if card])
        if hero_count > 0:
            print(f"\n🃏 Hero Cards ({hero_count}/2):")
            for region, card in hero_cards.items():
                if card:
                    print(f"  • {region}: {card}")
        else:
            print("\n🃏 Hero Cards: None detected")
        
        # Community cards by stage
        print(f"\n🌟 Community Cards ({stage.value}):")
        if stage_info['detected_cards']:
            for i, card in enumerate(stage_info['detected_cards'], 1):
                print(f"  • Card {i}: {card}")
        else:
            print("  • No community cards (Pre-Flop)")
        
        # Pot information
        if pot_value:
            print(f"\n💰 Pot Size: {pot_value}")
        else:
            print("\n💰 Pot Size: Not detected")
        
        # Tournament analysis
        if tournament_results and tournament_metrics and self.tournament_enabled:
            print(f"\n🏆 TOURNAMENT STATUS:")
            print(f"  • Active Players: {tournament_metrics['active_players']}/9")
            print(f"  • Total Chips: {tournament_metrics['total_chips']:,}")
            print(f"  • Average Stack: {tournament_metrics['average_stack']:,.0f}")
            
            if tournament_metrics['chip_leader']:
                leader = tournament_metrics['chip_leader']
                print(f"  • Chip Leader: {leader.name} ({leader.chips:,} chips)")
            
            if tournament_metrics['short_stack']:
                short = tournament_metrics['short_stack']
                print(f"  • Short Stack: {short.name} ({short.chips:,} chips)")
            
            # Hero tournament status
            hero = self.tournament_state.players[Position.HERO]
            if hero.chips:
                print(f"\n🎮 Hero Tournament Status:")
                print(f"  • Stack: {hero.chips:,} chips")
                if hero.bb_size:
                    print(f"  • Stack (BB): {hero.bb_size:.1f} BB")
                if tournament_metrics.get('hero_rank'):
                    print(f"  • Ranking: #{tournament_metrics['hero_rank']}/{tournament_metrics['active_players']}")
                print(f"  • Chip %: {tournament_metrics.get('hero_chip_percentage', 0):.1f}%")
            
            # Active player positions
            print(f"\n👥 Active Players:")
            for position, player in self.tournament_state.players.items():
                if player.name != "Empty" and player.chips:
                    status = "🎮" if position == Position.HERO else "🔴"
                    print(f"  {status} {position.value}: {player.name} ({player.chips:,} chips)")
        
        print("="*80)
    
    def print_poker_engine_results(self, enhanced_analysis):
        """Print poker engine analysis results."""
        if not enhanced_analysis or 'poker_analysis' not in enhanced_analysis:
            return
        
        poker_data = enhanced_analysis['poker_analysis']
        gui_display = enhanced_analysis.get('gui_display', {})
        
        print("\n" + "="*80)
        print("🧠 POKER ENGINE ANALYSIS")
        print("="*80)
        
        # Basic game state
        print(f"🎯 Game Stage: {poker_data.get('stage', 'Unknown')}")
        print(f"💰 Pot Size: ${poker_data.get('pot_size', 0):.2f}" if poker_data.get('pot_size') else "💰 Pot Size: Unknown")
        
        # Hero cards and hand evaluation
        hero_cards = poker_data.get('hero_cards', [])
        if hero_cards:
            print(f"🃏 Hero Cards: {' '.join(hero_cards)}")
        
        hand_eval = poker_data.get('hero_hand_evaluation')
        if hand_eval:
            print(f"🎲 Hand Ranking: {hand_eval['hand_name']}")
            print(f"📊 Hand Description: {hand_eval['description']}")
            print(f"💪 Hand Strength: {hand_eval['rank_score']}")
            print(f"🏆 Best 5 Cards: {' '.join(hand_eval['best_five_cards'])}")
        
        # Community cards
        community_cards = poker_data.get('community_cards', [])
        if community_cards:
            print(f"🌟 Community Cards: {' '.join(community_cards)}")
        
        # Deck analysis
        deck_analysis = poker_data.get('deck_analysis', {})
        if deck_analysis:
            print(f"\n🃏 DECK ANALYSIS:")
            print(f"   📝 Known Cards: {deck_analysis.get('known_cards', 0)}")
            print(f"   ❓ Unknown Cards: {deck_analysis.get('unknown_cards', 0)}")
            print(f"   👥 Estimated Active Players: {deck_analysis.get('estimated_active_players', 0)}")
            print(f"   🎴 Remaining Deck Size: {deck_analysis.get('remaining_deck_size', 0)}")
        
        # Probability analysis
        probability_analysis = enhanced_analysis.get('probability_analysis')
        if probability_analysis:
            print(f"\n🎲 PROBABILITY ANALYSIS:")
            
            # Equity information
            equity = probability_analysis.get('equity', {})
            if equity:
                win_pct = equity.get('win_percentage', 0)
                tie_pct = equity.get('tie_percentage', 0)
                lose_pct = equity.get('lose_percentage', 0)
                print(f"   📊 Win: {win_pct:.1f}% | Tie: {tie_pct:.1f}% | Lose: {lose_pct:.1f}%")
            
            # Opponent analysis
            opponent_analysis = probability_analysis.get('opponent_analysis', {})
            if opponent_analysis.get('average_hand_strength'):
                avg_strength = opponent_analysis['average_hand_strength']
                print(f"   🎯 Opponent Avg Strength: {avg_strength:.0f}")
            
            # Board texture
            board_texture = probability_analysis.get('board_texture', {})
            if board_texture:
                draws = []
                if board_texture.get('flush_draw_possible'): draws.append("Flush")
                if board_texture.get('straight_draw_possible'): draws.append("Straight")
                if board_texture.get('paired_board'): draws.append("Paired")
                
                if draws:
                    print(f"   ⚠️ Board Texture: {', '.join(draws)}")
                
                wetness = board_texture.get('board_wetness', 'Unknown')
                print(f"   🌊 Board Wetness: {wetness}")
        
        # Performance metrics
        processing_time = poker_data.get('processing_time_ms', 0)
        print(f"\n⚡ Poker Engine Time: {processing_time:.2f}ms")
        
        print("="*80)
    
    def print_fast_analysis_results(self, hero_cards, community_cards, pot_value, stage_info, analysis_time):
        """Print fast analysis results for immediate decision making."""
        print("\n" + "="*60)
        print(f"⚡ FAST POKER ANALYSIS - Hand #{self.hand_count}")
        print(f"🚀 Analysis Time: {analysis_time:.1f}ms")
        print("="*60)
        
        # Stage information
        stage = stage_info['stage']
        print(f"🎯 Stage: {stage.value} ({stage_info['confidence']:.0%} confidence)")
        
        # Hero cards
        hero_count = len([card for card in hero_cards.values() if card])
        if hero_count > 0:
            hero_cards_list = [card for card in hero_cards.values() if card]
            print(f"🃏 Hero: {' '.join(hero_cards_list)}")
        else:
            print("🃏 Hero: No cards detected")
        
        # Community cards
        if stage_info['detected_cards']:
            community_list = ' '.join(stage_info['detected_cards'])
            print(f"🌟 Board: {community_list}")
        else:
            print("🌟 Board: Empty (Pre-Flop)")
        
        # Pot
        if pot_value:
            print(f"💰 Pot: {pot_value}")
        else:
            print("💰 Pot: Not detected")
        
        print("="*60)
    
    def ocr_card_region(self, region, region_name=None):
        """OCR analysis for card regions with learning system integration."""
        if region is None or region.size == 0:
            return None
            
        try:
            # First check if there's actually a card present
            if not self.is_card_present(region):
                print("❌ No card detected in region")
                return None
            
            # If card is present, proceed with detection (now includes learning lookup)
            return self.detect_card_value(region, region_name)
            
        except Exception as e:
            print(f"❌ OCR card region error: {e}")
            return None
    
    def is_card_present(self, region):
        """Determine if there's actually a card present in the region."""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
            
            # Multiple checks for card presence
            
            # 1. Check contrast - cards have high contrast between text and background
            contrast = gray.std()
            print(f"   📊 Contrast: {contrast:.1f}")
            
            # 2. Check edge density - cards have clear edges
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            print(f"   📊 Edge density: {edge_density:.3f}")
            
            # 3. Check brightness distribution - cards are typically white/light with dark text
            mean_brightness = np.mean(gray)
            print(f"   📊 Mean brightness: {mean_brightness:.1f}")
            
            # 4. Check for rectangular card outline
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            large_contours = [c for c in contours if cv2.contourArea(c) > 100]
            has_card_shape = len(large_contours) > 0
            print(f"   📊 Large contours: {len(large_contours)}")
            
            # Card presence criteria (conservative thresholds)
            card_present = (
                contrast > 15 and          # Must have some contrast
                edge_density > 0.01 and    # Must have some edges
                mean_brightness > 80 and   # Must be reasonably bright
                has_card_shape             # Must have some structure
            )
            
            print(f"   🎴 Card present: {card_present}")
            return card_present
            
        except Exception as e:
            print(f"   ❌ Card presence check failed: {e}")
            return False  # Conservative: if check fails, assume no card
    
    def detect_card_value(self, card_region, region_name=None):
        """Detect card rank and suit using learned cards first, then OCR fallback."""
        try:
            # Fast lookup from learning database first
            if region_name:
                learned_card = self.lookup_learned_card(card_region, region_name)
                if learned_card:
                    return learned_card
            
            # Fallback to OCR detection
            # Convert to color if needed
            if len(card_region.shape) == 3:
                color_region = card_region
                gray_region = cv2.cvtColor(card_region, cv2.COLOR_BGR2GRAY)
            else:
                gray_region = card_region
                color_region = None
                
            height, width = gray_region.shape
            if height < 20 or width < 20:
                return None
            
            # First detect rank using OCR
            rank = self.detect_card_rank(gray_region)
            
            # Then detect suit using color analysis
            suit = self.detect_card_suit_by_color(color_region) if color_region is not None else None
            
            # Combine rank and suit
            if rank and suit:
                result = f"{rank}{suit}"
                print(f"🎯 Card detected: {result} (rank: {rank}, suit: {suit})")
                return result
            elif rank:
                # Fallback to spades if suit detection fails
                result = f"{rank}♠"
                print(f"🎯 Card detected: {result} (rank: {rank}, suit fallback)")
                return result
            elif suit:
                # If we have suit but no rank, try a more aggressive OCR approach
                fallback_rank = self.detect_rank_fallback(gray_region)
                if fallback_rank:
                    result = f"{fallback_rank}{suit}"
                    print(f"🎯 Card detected: {result} (fallback rank: {fallback_rank}, suit: {suit})")
                    return result
                else:
                    print(f"❌ Card detection failed - suit detected ({suit}) but no rank")
            else:
                print("❌ Card detection failed")
                
        except Exception as e:
            print(f"❌ detect_card_value error: {e}")
        
        # Fallback: Template matching approach
        return self.detect_card_by_template(gray_region)
    
    def lookup_learned_card(self, card_region, region_name):
        """Look up a card from the learning database for faster recognition."""
        try:
            import hashlib
            import json
            from datetime import datetime
            
            learning_file = 'card_learning_data.json'
            if not os.path.exists(learning_file):
                return None
                
            # Generate card image hash for lookup
            card_hash = self.get_card_image_hash(card_region)
            if not card_hash:
                return None
                
            with open(learning_file, 'r') as f:
                data = json.load(f)
            
            if card_hash in data.get('card_database', {}):
                card_data = data['card_database'][card_hash]
                
                # Add this region to regions where card was used
                if 'regions_used' not in card_data:
                    card_data['regions_used'] = []
                if region_name not in card_data['regions_used']:
                    card_data['regions_used'].append(region_name)
                
                # Increment usage count
                card_data['usage_count'] = card_data.get('usage_count', 0) + 1
                card_data['last_used'] = datetime.now().isoformat()
                card_data['last_used_region'] = region_name
                
                # Save updated usage
                with open(learning_file, 'w') as f:
                    json.dump(data, f, indent=2)
                
                regions_used = len(card_data.get('regions_used', []))
                print(f"🎯 Universal lookup: {card_data['card']} (used {card_data['usage_count']} times across {regions_used} regions)")
                return card_data['card']
                
        except Exception as e:
            print(f"❌ Error looking up learned card: {e}")
            
        return None
    
    def get_card_image_hash(self, card_region):
        """Generate a hash of the card image for duplicate detection."""
        try:
            import hashlib
            import cv2
            
            # Resize to standard size for consistent hashing
            card_img = cv2.resize(card_region, (100, 150))
            
            # Convert to grayscale for consistent comparison
            if len(card_img.shape) == 3:
                gray = cv2.cvtColor(card_img, cv2.COLOR_BGR2GRAY)
            else:
                gray = card_img
            
            # Apply slight blur to reduce noise differences
            gray = cv2.GaussianBlur(gray, (3, 3), 0)
            
            # Calculate hash using image content
            img_hash = hashlib.md5(gray.tobytes()).hexdigest()
            return img_hash
            
        except Exception as e:
            print(f"❌ Error generating card hash: {e}")
            return None
    
    def detect_card_rank(self, gray_region):
        """Detect card rank using enhanced OCR with multiple preprocessing approaches."""
        try:
            import pytesseract
            # Set Tesseract path for Windows
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            
            height, width = gray_region.shape
            
            # Try multiple regions for rank detection
            regions_to_try = [
                # Top-left corner (most common)
                gray_region[:height//2, :width//2],
                # Top-left smaller
                gray_region[:height//3, :width//3],
                # Slightly larger top area
                gray_region[:2*height//3, :width//2],
                # Full top row
                gray_region[:height//4, :],
            ]
            
            rank_map = {
                'A': 'A', 'K': 'K', 'Q': 'Q', 'J': 'J',
                '2': '2', '3': '3', '4': '4', '5': '5', '6': '6', 
                '7': '7', '8': '8', '9': '9', '10': 'T',  # Map "10" to "T" for display
                # Common OCR misreadings for numbers
                'B': '8', 'G': '6', 'S': '5', 'I': '1', 'O': '0', 
                'D': '0', 'Z': '2', 'L': '1', 'R': '2'
            }
            
            # Special handling for A/4 and Q/8 confusion
            def resolve_ambiguous_chars(ocr_text, region):
                """Resolve A/4 and Q/8 confusion using shape analysis"""
                result_chars = []
                
                for char in ocr_text.upper():
                    if char in ['A', '4']:
                        # Distinguish A from 4 using shape analysis
                        resolved = distinguish_A_from_4(region)
                        result_chars.append(resolved if resolved is not None else char)
                    elif char in ['Q', '8']:
                        # Distinguish Q from 8 using shape analysis
                        resolved = distinguish_Q_from_8(region)
                        result_chars.append(resolved if resolved is not None else char)
                    else:
                        result_chars.append(char)
                
                return ''.join(result_chars)
            
            def distinguish_A_from_4(region):
                """Distinguish between A and 4 using shape features"""
                try:
                    # Apply strong threshold to get clear shapes
                    _, binary = cv2.threshold(region, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    
                    # Find contours
                    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    
                    if not contours:
                        return None
                    
                    # Get the largest contour (main character)
                    main_contour = max(contours, key=cv2.contourArea)
                    
                    # Calculate bounding rectangle
                    _, _, w, h = cv2.boundingRect(main_contour)
                    aspect_ratio = h / w if w > 0 else 0
                    
                    # Calculate moments for shape analysis
                    moments = cv2.moments(main_contour)
                    
                    # Different approach: check the horizontal distribution
                    # A has a peak at top, 4 has a vertical line on the right
                    hist_horizontal = np.sum(binary, axis=0)  # Sum columns
                    hist_vertical = np.sum(binary, axis=1)    # Sum rows
                    
                    # Normalize histograms
                    if np.max(hist_horizontal) > 0:
                        hist_horizontal = hist_horizontal / np.max(hist_horizontal)
                    if np.max(hist_vertical) > 0:
                        hist_vertical = hist_vertical / np.max(hist_vertical)
                    
                    # A typically has more distributed horizontal content (triangle shape)
                    # 4 has a strong peak on the right (vertical line)
                    right_third = len(hist_horizontal) * 2 // 3
                    right_intensity = np.mean(hist_horizontal[right_third:]) if right_third < len(hist_horizontal) else 0
                    left_intensity = np.mean(hist_horizontal[:len(hist_horizontal)//3])
                    
                    # 4 typically has higher intensity on the right side
                    right_dominance = right_intensity / (left_intensity + 0.1)
                    
                    print(f"   🔬 A/4 analysis: aspect_ratio={aspect_ratio:.2f}, right_dominance={right_dominance:.2f}")
                    
                    # If right side is much stronger, it's likely a 4
                    # Narrowed range based on data: 4's show 0.80-0.85, A shows 1.18
                    if 0.75 < right_dominance < 0.95 and aspect_ratio < 0.7:
                        return '4'
                    # If more balanced horizontally and triangular, it's likely an A
                    elif right_dominance < 0.6 or right_dominance > 1.1:
                        return 'A'
                    else:
                        # More conservative fallback: if in doubt, keep the original OCR result
                        # Only override if we have strong shape evidence
                        return None  # Let original OCR result stand
                        
                except Exception as e:
                    print(f"   ❌ A/4 analysis failed: {e}")
                return None
            
            def distinguish_Q_from_8(region):
                """Distinguish between Q and 8 using shape features"""
                try:
                    # Apply threshold
                    _, binary = cv2.threshold(region, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    
                    # Find contours
                    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    
                    if not contours:
                        return None
                    
                    # Count significant contours (holes)
                    significant_contours = [c for c in contours if cv2.contourArea(c) > 10]
                    
                    print(f"   🔬 Q/8 analysis: {len(significant_contours)} contours")
                    
                    # 8 typically has 2 holes/loops, Q has 1
                    if len(significant_contours) >= 3:  # Main shape + 2 holes
                        return '8'
                    elif len(significant_contours) == 2:  # Main shape + 1 hole
                        return 'Q'
                        
                    # Alternative: check for the Q's tail using moments
                    main_contour = max(contours, key=cv2.contourArea)
                    moments = cv2.moments(main_contour)
                    
                    # Q is typically more asymmetric due to the tail
                    if moments['m00'] > 0:
                        skewness = moments['mu11'] / (moments['m00'] * 0.001 + 1e-10)
                        print(f"   🔬 Q/8 skewness: {skewness:.2f}")
                        if abs(skewness) > 5:  # Q has more skew due to tail
                            return 'Q'
                        else:
                            return '8'
                            
                except Exception as e:
                    print(f"   ❌ Q/8 analysis failed: {e}")
                return None
            
            
            # Try different preprocessing and OCR configurations
            configs = [
                '--psm 10 -c tessedit_char_whitelist=AKQJ1023456789',  # Single character (includes 10)
                '--psm 8 -c tessedit_char_whitelist=AKQJ1023456789',   # Single textline (includes 10)
                '--psm 7 -c tessedit_char_whitelist=AKQJ1023456789',   # Single text block (includes 10)
                '--psm 6 -c tessedit_char_whitelist=AKQJ1023456789',   # Single uniform block (includes 10)
            ]
            
            for region_idx, rank_region in enumerate(regions_to_try):
                if rank_region.size == 0:
                    continue
                    
                # Try different preprocessing approaches
                preprocessed_images = []
                
                # 1. High contrast with different scaling
                for scale in [3, 4, 5]:
                    resized = cv2.resize(rank_region, (rank_region.shape[1]*scale, rank_region.shape[0]*scale), 
                                       interpolation=cv2.INTER_CUBIC)
                    # OTSU threshold
                    _, thresh1 = cv2.threshold(resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    preprocessed_images.append(thresh1)
                    
                    # Fixed threshold
                    _, thresh2 = cv2.threshold(resized, 127, 255, cv2.THRESH_BINARY)
                    preprocessed_images.append(thresh2)
                    
                    # Inverted
                    _, thresh3 = cv2.threshold(resized, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
                    preprocessed_images.append(thresh3)
                
                # Try each preprocessed image with each config
                for img_idx, processed_img in enumerate(preprocessed_images):
                    for config_idx, config in enumerate(configs):
                        try:
                            ocr_result = pytesseract.image_to_string(processed_img, config=config).strip()
                            
                            # Debug output
                            print(f"🔍 Region {region_idx+1}, Preprocess {img_idx+1}, Config {config_idx+1}: '{ocr_result}'")
                            
                            if ocr_result:
                                # Apply ambiguous character resolution for A/4 and Q/8
                                resolved_text = resolve_ambiguous_chars(ocr_result, rank_region)
                                print(f"🔧 After ambiguous resolution: '{resolved_text}'")
                                
                                # Look for valid ranks in the result
                                for char in resolved_text.upper():
                                    if char in rank_map:
                                        detected_rank = rank_map[char]
                                        print(f"✅ Rank detected: {detected_rank}")
                                        return detected_rank
                                        
                        except Exception as e:
                            continue
                    
        except Exception as e:
            print(f"❌ Rank detection error: {e}")
        
        return None
    
    def detect_rank_fallback(self, gray_region):
        """Fallback rank detection with more aggressive preprocessing."""
        try:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            
            height, width = gray_region.shape
            
            # Try different preprocessing approaches
            approaches = [
                # Approach 1: Different threshold
                lambda img: cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)[1],
                # Approach 2: Adaptive threshold
                lambda img: cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2),
                # Approach 3: Morphological operations
                lambda img: cv2.morphologyEx(cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1], 
                                           cv2.MORPH_CLOSE, np.ones((2,2), np.uint8))
            ]
            
            rank_map = {
                'A': 'A', 'K': 'K', 'Q': 'Q', 'J': 'J',
                '2': '2', '3': '3', '4': '4', '5': '5', '6': '6', 
                '7': '7', '8': '8', '9': '9', '10': 'T',  # Map "10" to "T" for display
                # Common OCR misreadings for numbers
                'B': '8', 'G': '6', 'S': '5', 'I': '1', 'O': '0', 
                'D': '0', 'Z': '2', 'L': '1', 'R': '2'
            }
            
            for i, approach in enumerate(approaches):
                try:
                    processed = approach(gray_region)
                    resized = cv2.resize(processed, (processed.shape[1]*3, processed.shape[0]*3), 
                                       interpolation=cv2.INTER_CUBIC)
                    
                    config = '--psm 8 -c tessedit_char_whitelist=AKQJ1023456789'
                    ocr_result = pytesseract.image_to_string(resized, config=config).strip()
                    
                    print(f"🔄 Fallback approach {i+1}: '{ocr_result}'")
                    
                    for char in ocr_result.upper():
                        if char in rank_map:
                            return rank_map[char]
                            
                except Exception as e:
                    print(f"❌ Fallback approach {i+1} failed: {e}")
                    continue
                    
        except Exception as e:
            print(f"❌ Fallback rank detection error: {e}")
        
        return None
    
    def detect_card_suit_by_color(self, color_region):
        """Detect card suit by analyzing colors in the image."""
        try:
            if color_region is None:
                return None
                
            height, width = color_region.shape[:2]
            
            # Focus on the suit area (typically bottom-right or below rank)
            suit_region = color_region[height//4:3*height//4, width//4:3*width//4]
            
            # Convert to HSV for better color analysis
            hsv = cv2.cvtColor(suit_region, cv2.COLOR_BGR2HSV)
            
            # Define color ranges for suits
            # Red range (Hearts ♥)
            red_lower1 = np.array([0, 50, 50])
            red_upper1 = np.array([10, 255, 255])
            red_lower2 = np.array([170, 50, 50])
            red_upper2 = np.array([180, 255, 255])
            
            # Green range (Clubs ♣) 
            green_lower = np.array([40, 50, 50])
            green_upper = np.array([80, 255, 255])
            
            # Blue range (Diamonds ♦)
            blue_lower = np.array([100, 50, 50])
            blue_upper = np.array([130, 255, 255])
            
            # Create masks for each color
            red_mask1 = cv2.inRange(hsv, red_lower1, red_upper1)
            red_mask2 = cv2.inRange(hsv, red_lower2, red_upper2)
            red_mask = cv2.bitwise_or(red_mask1, red_mask2)
            
            green_mask = cv2.inRange(hsv, green_lower, green_upper)
            blue_mask = cv2.inRange(hsv, blue_lower, blue_upper)
            
            # Count pixels for each color
            red_pixels = cv2.countNonZero(red_mask)
            green_pixels = cv2.countNonZero(green_mask)
            blue_pixels = cv2.countNonZero(blue_mask)
            
            print(f"🎨 Color analysis - Red: {red_pixels}, Green: {green_pixels}, Blue: {blue_pixels}")
            
            # Determine suit based on dominant color
            max_pixels = max(red_pixels, green_pixels, blue_pixels)
            
            if max_pixels < 10:  # Too few colored pixels, likely black (spades)
                return '♠'
            elif red_pixels == max_pixels:
                return '♥'
            elif green_pixels == max_pixels:
                return '♣'
            elif blue_pixels == max_pixels:
                return '♦'
            else:
                return '♠'  # Default to spades
                
        except Exception as e:
            print(f"❌ Suit detection error: {e}")
            return '♠'  # Default fallback
                
        except Exception as e:
            print(f"Card detection error: {e}")
            return None
    
    def clean_card_text(self, text):
        """Clean OCR text to extract card information."""
        # Remove common OCR noise
        text = text.replace('|', '').replace('-', '').replace('_', '')
        text = text.replace('O', '0').replace('l', '1').replace('S', '5')
        
        # Look for card patterns
        suits = {'♠': '♠', '♥': '♥', '♦': '♦', '♣': '♣', 
                's': '♠', 'h': '♥', 'd': '♦', 'c': '♣'}
        ranks = {'A': 'A', 'K': 'K', 'Q': 'Q', 'J': 'J', 'T': '10',
                '2': '2', '3': '3', '4': '4', '5': '5', '6': '6', 
                '7': '7', '8': '8', '9': '9', '10': '10'}
        
        # Extract rank and suit
        rank = None
        suit = None
        
        for char in text.upper():
            if char in ranks and rank is None:
                rank = ranks[char]
            elif char.lower() in suits and suit is None:
                suit = suits[char.lower()]
        
        if rank and suit:
            return f"{rank}{suit}"
        elif rank:
            # If we have rank but no suit, try to guess or return with spades
            return f"{rank}♠"
        
        return None
    
    def detect_card_by_template(self, gray_region):
        """Fallback template-based card detection."""
        try:
            # Simple edge-based detection as fallback
            edges = cv2.Canny(gray_region, 50, 150)
            edge_count = np.sum(edges > 0)
            
            # This is still a placeholder - would need proper templates
            if edge_count > 200:
                return "A♠"
            elif edge_count > 150:
                return "K♥"
            elif edge_count > 100:
                return "Q♦"
            elif edge_count > 50:
                return "J♣"
            else:
                return None
                
        except Exception:
            return None
    
    def ocr_text_region(self, region):
        """OCR analysis for text regions (like pot amount)."""
        if region is None or region.size == 0:
            return None
            
        try:
            # Check if tesseract is available
            try:
                import pytesseract
                # Set Tesseract path for Windows
                pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
                
                # Preprocess for text recognition
                gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
                enhanced = cv2.convertScaleAbs(gray, alpha=2.0, beta=0)
                
                # Use PSM 7 (single line) which works better for pot text
                config = '--psm 7 -c tessedit_char_whitelist=0123456789$.,PotBb:, '
                text = pytesseract.image_to_string(enhanced, config=config).strip()
                
                print(f"🔍 Raw pot OCR: '{text}'")
                
                # Parse pot text that should be in format "Pot: X,X BB" or "Pot: X.X BB"
                if text:
                    import re
                    # Look for European format numbers (comma as decimal separator)
                    # Pattern matches: "3,5", "52.2", "100", etc.
                    number_match = re.search(r'(\d+[,.]\d+|\d+)', text)
                    if number_match:
                        pot_value = number_match.group(1).replace(',', '.')  # Convert European format
                        print(f"🎯 Extracted pot value: {pot_value}")
                        return pot_value
                
                return text if text else None
                
            except ImportError:
                # Fallback without tesseract
                mean_intensity = np.mean(region)
                return f"${int(mean_intensity * 10)}" if mean_intensity > 50 else None
                
        except Exception as e:
            print(f"Text OCR error: {e}")
            return None
    
    def ocr_stack_region(self, region):
        """OCR analysis specifically for stack amount regions."""
        if region is None or region.size == 0:
            return None
            
        try:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            
            # Preprocess for better OCR of stack numbers
            gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
            
            # Enhance contrast
            enhanced = cv2.convertScaleAbs(gray, alpha=2.0, beta=0)
            
            # Scale up for better OCR
            scale_factor = 3
            height, width = enhanced.shape
            resized = cv2.resize(enhanced, (width * scale_factor, height * scale_factor), interpolation=cv2.INTER_CUBIC)
            
            # Apply threshold
            _, thresh = cv2.threshold(resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # OCR with configuration for numbers and BB
            config = '--psm 7 -c tessedit_char_whitelist=0123456789.,KkBb '
            text = pytesseract.image_to_string(thresh, config=config).strip()
            
            print(f"🔍 Stack OCR: '{text}'")
            return text if text else None
            
        except Exception as e:
            print(f"❌ Stack OCR error: {e}")
            return None
    
    def ocr_name_region(self, region):
        """OCR analysis specifically for player name regions."""
        if region is None or region.size == 0:
            return None
            
        try:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            
            # Preprocess for player names
            gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
            
            # Enhance contrast
            enhanced = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)
            
            # Scale up for better OCR
            scale_factor = 2
            height, width = enhanced.shape
            resized = cv2.resize(enhanced, (width * scale_factor, height * scale_factor), interpolation=cv2.INTER_CUBIC)
            
            # Apply threshold
            _, thresh = cv2.threshold(resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # OCR with configuration for names (letters, numbers, underscores)
            config = '--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_'
            text = pytesseract.image_to_string(thresh, config=config).strip()
            
            print(f"🔍 Name OCR: '{text}'")
            return text if text else None
            
        except Exception as e:
            print(f"❌ Name OCR error: {e}")
            return None
    
    def _parse_player_data(self, name_text, stack_text, position):
        """Parse OCR text into structured player data."""
        player = PlayerStack(
            name="Unknown",
            position=position,
            last_updated=time.time()
        )
        
        # Parse player name
        if name_text:
            # Clean up name text
            cleaned_name = re.sub(r'[^a-zA-Z0-9_]', '', name_text.strip())
            if cleaned_name and len(cleaned_name) > 2:
                player.name = cleaned_name
                player.confidence += 0.3
        
        # Parse stack size
        if stack_text:
            chips, bb_value = self._parse_stack_text(stack_text)
            if chips:
                player.chips = chips
                player.bb_size = bb_value
                player.confidence += 0.7
        
        return player
    
    def _parse_stack_text(self, stack_text):
        """Parse stack text to extract chip count and BB value."""
        if not stack_text:
            return None, None
        
        # Look for chip patterns (e.g., "1,500", "750", "12.5K")
        chip_patterns = [
            r'(\d{1,3}(?:,\d{3})+)',  # 1,500 format
            r'(\d+\.?\d*)\s*[Kk]',    # 12.5K format
            r'(\d+)',                 # Simple number
        ]
        
        # Look for BB patterns (e.g., "85.5 BB", "99BB")
        bb_patterns = [
            r'(\d+\.?\d*)\s*BB',      # 85.5 BB format
            r'(\d+\.?\d*)BB',         # 99BB format
        ]
        
        chips = None
        bb_value = None
        
        # Try to extract chip count
        for pattern in chip_patterns:
            match = re.search(pattern, stack_text)
            if match:
                chip_str = match.group(1).replace(',', '')
                try:
                    if 'K' in stack_text.upper():
                        chips = int(float(chip_str) * 1000)
                    else:
                        chips = int(chip_str)
                    break
                except ValueError:
                    continue
        
        # Try to extract BB value
        for pattern in bb_patterns:
            match = re.search(pattern, stack_text)
            if match:
                try:
                    bb_value = float(match.group(1))
                    break
                except ValueError:
                    continue
        
        return chips, bb_value
    
    def update_tournament_state(self, stack_results):
        """Update internal tournament state with new data and detect eliminations."""
        # First, detect eliminations before updating
        eliminations = self.detect_player_elimination(stack_results)
        
        # Update active players
        for position, player_data in stack_results.items():
            if player_data and player_data.confidence > 0.5:
                self.tournament_state.players[position] = player_data
        
        self.tournament_state.last_update = time.time()
        
        # Update total chips if we have enough data
        active_players = [
            player for player in self.tournament_state.players.values()
            if player.chips and player.name != "Empty" and player.chips > 0
        ]
        
        if active_players:
            total_chips = sum(player.chips for player in active_players)
            self.tournament_state.total_chips = total_chips
            
            # Log tournament progression
            active_count = len(active_players)
            if eliminations:
                print(f"🏆 Tournament Update: {active_count} players remaining")
                for elimination in eliminations:
                    print(f"   💀 {elimination['player_name']} eliminated")
        
        return eliminations
    
    def calculate_tournament_metrics(self):
        """Calculate comprehensive tournament metrics."""
        active_players = [
            player for player in self.tournament_state.players.values()
            if player.chips and player.name != "Empty"
        ]
        
        if not active_players:
            return {}
        
        # Sort by chip count
        sorted_players = sorted(active_players, key=lambda p: p.chips, reverse=True)
        
        # Calculate metrics
        total_chips = sum(p.chips for p in active_players)
        hero = self.tournament_state.players[Position.HERO]
        
        metrics = {
            'active_players': len(active_players),
            'total_chips': total_chips,
            'chip_leader': sorted_players[0] if sorted_players else None,
            'short_stack': sorted_players[-1] if sorted_players else None,
            'average_stack': total_chips / len(active_players) if active_players else 0,
            'hero_rank': None,
            'hero_chip_percentage': 0.0,
            'players_by_rank': sorted_players
        }
        
        # Hero-specific metrics
        if hero.chips:
            hero_rank = next(
                (i + 1 for i, p in enumerate(sorted_players) if p.position == Position.HERO),
                None
            )
            metrics['hero_rank'] = hero_rank
            metrics['hero_chip_percentage'] = (hero.chips / total_chips) * 100 if total_chips > 0 else 0
        
        return metrics
    
    def detect_player_elimination(self, new_stack_results):
        """Detect when players are eliminated from the tournament."""
        eliminations = []
        
        # Check each position for elimination
        for position in Position:
            current_player = self.tournament_state.players.get(position)
            new_player = new_stack_results.get(position)
            
            # Player was active but now missing or has no chips
            if (current_player and current_player.name != "Empty" and current_player.chips and current_player.chips > 0):
                if (not new_player or new_player.chips is None or new_player.chips <= 0 or 
                    self._is_empty_seat(position, new_player)):
                    eliminations.append({
                        'position': position,
                        'player_name': current_player.name,
                        'last_stack': current_player.chips,
                        'elimination_time': time.time()
                    })
                    
                    # Mark as eliminated
                    self.tournament_state.players[position] = PlayerStack(
                        name="Empty",
                        position=position,
                        last_updated=time.time()
                    )
                    
                    print(f"🚫 PLAYER ELIMINATED: {current_player.name} at {position.value}")
        
        return eliminations
    
    def _is_empty_seat(self, position, player_data):
        """Check if a seat appears empty (background showing instead of player)."""
        if not player_data:
            return True
            
        # Check for typical "empty seat" indicators
        empty_indicators = [
            player_data.name in ["Empty", "Unknown", ""],
            player_data.chips is None or player_data.chips <= 0,
            player_data.confidence < 0.3  # Very low confidence suggests no player data
        ]
        
        return any(empty_indicators)
    
    def get_active_player_count(self):
        """Get current count of active players."""
        return len([
            player for player in self.tournament_state.players.values()
            if player.chips and player.name != "Empty" and player.chips > 0
        ])
    
    def draw_regions_overlay(self, frame):
        """Draw region overlays on frame."""
        overlay = frame.copy()
        
        for region_name, coords in self.current_regions.items():
            if len(coords) != 4:
                continue
                
            x, y, w, h = coords
            
            # Color coding
            if 'hero' in region_name:
                color = (0, 255, 0)  # Green
            elif 'community' in region_name:
                color = (255, 0, 0)  # Blue
            elif 'pot' in region_name:
                color = (0, 255, 255)  # Yellow
            else:
                color = (128, 128, 128)  # Gray
            
            # Draw rectangle
            cv2.rectangle(overlay, (x, y), (x + w, y + h), color, 2)
            
            # Add label
            label = region_name.replace('_', ' ').title()
            cv2.putText(overlay, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        return overlay

# Legacy compatibility
SmartPokerBot = SimplePokerBot
