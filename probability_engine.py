#!/usr/bin/env python3
"""
Probability Engine for Poker Hand Estimation

This module calculates probabilities and estimates opponent holdings based on:
- Known cards (hero + community + revealed opponent cards)
- Remaining deck composition
- Active player count
- Board texture analysis

Features:
- Dynamic probability calculation for each stage (Flop, Turn, River)
- Opponent hand strength estimation
- Board texture analysis (draws, pairs, etc.)
- Equity calculation (win/lose/tie percentages)
- Monte Carlo simulation for complex scenarios
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import itertools
import random

class ProbabilityEngine:
    """Advanced probability calculation engine for poker analysis."""
    
    def __init__(self):
        """Initialize the probability engine with deck and hand rankings."""
        self.suits = ['♠', '♥', '♦', '♣']
        self.ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
        self.rank_values = {rank: i for i, rank in enumerate(self.ranks)}
        
        # Generate full deck
        self.full_deck = []
        for rank in self.ranks:
            for suit in self.suits:
                self.full_deck.append(f"{rank}{suit}")
        
        # Hand reset tracking
        self.last_community_count = 0
        self.last_stage = None
        self.hand_session_data = {}
    
    def calculate_hand_probabilities(self, hero_cards: List[str], community_cards: List[str], 
                                   active_opponents: int, known_opponent_cards: List[str] = None,
                                   total_active_players: int = None) -> Dict:
        """
        Calculate comprehensive hand probabilities and opponent estimations.
        
        Args:
            hero_cards: List of hero's hole cards (e.g., ['A♠', 'K♥'])
            community_cards: List of community cards (e.g., ['Q♣', 'J♦', 'T♠'])
            active_opponents: Number of active opponents in betting round
            known_opponent_cards: Optional list of known opponent cards
            total_active_players: Total active seated players for deck calculation
            
        Returns:
            Dictionary with equity, opponent analysis, board texture, etc.
        """
        if not hero_cards or len(hero_cards) != 2:
            return {'error': 'Invalid hero cards'}
        
        if len(community_cards) > 5:
            return {'error': 'Too many community cards'}
        
        # Detect hand reset (new preflop)
        current_stage = self._determine_stage(len(community_cards))
        hand_reset_detected = self._detect_hand_reset(current_stage, len(community_cards))
        
        if hand_reset_detected:
            print("🔄 NEW HAND DETECTED: Resetting probability analysis state")
            self.hand_session_data = {}
        
        # Calculate deck information accounting for all active seated players
        if total_active_players is not None:
            # Use total active players for deck calculation (includes all seated active players)
            total_player_cards = total_active_players * 2
            remaining_deck_size = 52 - len(community_cards) - total_player_cards
            print(f"🃏 DECK STATE: Total Active Players: {total_active_players}, Community: {len(community_cards)}, "
                  f"Player Cards: {total_player_cards}, Remaining: {remaining_deck_size}/52")
        else:
            # Fallback to old calculation if total_active_players not provided
            opponent_cards_count = active_opponents * 2
            total_player_cards = len(hero_cards) + opponent_cards_count
            total_known_cards = len(hero_cards) + len(community_cards) + opponent_cards_count
            remaining_deck_size = 52 - total_known_cards
            print(f"🃏 DECK STATE: Hero: {len(hero_cards)}, Community: {len(community_cards)}, "
                  f"Opponents: {active_opponents} × 2 = {opponent_cards_count}, Remaining: {remaining_deck_size}/52")
        
        # Analyze hero hand
        hero_analysis = self._analyze_hero_hand(hero_cards, community_cards)
        
        # Analyze opponent possibilities with player count consideration
        opponent_analysis = self._analyze_opponent_possibilities(
            hero_cards, community_cards, active_opponents, known_opponent_cards
        )
        
        # Analyze board texture with player count consideration
        board_texture = self._analyze_board_texture(community_cards, active_opponents)
        
        # Calculate player-count-aware equity
        equity = self._calculate_simple_equity(hero_cards, community_cards, active_opponents)
        
        # Calculate draws
        draws = self._calculate_draws(hero_cards, community_cards)
        
        # Store current state for next iteration
        self.last_community_count = len(community_cards)
        self.last_stage = current_stage
        
        return {
            'game_stage': current_stage,
            'hand_reset_detected': hand_reset_detected,
            'deck_info': {
                'total_deck_size': 52,
                'hero_cards': len(hero_cards),
                'community_cards': len(community_cards),
                'opponent_cards': total_player_cards if total_active_players else active_opponents * 2,
                'remaining_cards': remaining_deck_size,
                'active_opponents': active_opponents,
                'total_active_players': total_active_players
            },
            'hero_analysis': hero_analysis,
            'opponent_analysis': opponent_analysis,
            'board_texture': board_texture,
            'equity': equity,
            'draws': draws,
            'simulation_count': 1000  # Default simulation count
        }
    
    def _detect_hand_reset(self, current_stage: str, community_count: int) -> bool:
        """
        Detect if a new hand has started (reset to preflop).
        
        Returns True if:
        1. We're in preflop (0 community cards) and last time we had community cards
        2. This is the first analysis of the session
        """
        # First time running
        if self.last_stage is None:
            return True
        
        # Reset detected: we had community cards, now we're back to preflop
        if current_stage == 'Preflop' and self.last_community_count > 0:
            return True
        
        # No reset detected
        return False
    
    def _determine_stage(self, community_count: int) -> str:
        """Determine the current game stage."""
        if community_count == 0:
            return 'Preflop'
        elif community_count == 3:
            return 'Flop'
        elif community_count == 4:
            return 'Turn'
        elif community_count == 5:
            return 'River'
        else:
            return 'Unknown'
    
    def _analyze_hero_hand(self, hero_cards: List[str], community_cards: List[str]) -> Dict:
        """Analyze hero's current hand strength and potential."""
        try:
            from poker_engine import HandEvaluator, Card
            
            evaluator = HandEvaluator()
            
            # Convert string cards to Card objects
            def string_to_card(card_str: str):
                return Card.from_string(card_str)
            
            # Current best hand (use all available cards)
            all_cards = hero_cards + community_cards
            if len(all_cards) >= 5:
                all_card_objects = [string_to_card(card) for card in all_cards]
                current_hand = evaluator.evaluate_hand(all_card_objects)
                
                return {
                    'hand_ranking': current_hand.hand_name,
                    'hand_description': current_hand.description,
                    'hand_strength': current_hand.rank_score,
                    'best_five_cards': [str(card) for card in current_hand.best_five_cards]
                }
            else:
                # For incomplete hands, evaluate potential
                return {
                    'hand_ranking': 'Incomplete',
                    'hand_description': 'Draw',
                    'hand_strength': 0,
                    'best_five_cards': all_cards
                }
        except Exception as e:
            return {
                'hand_ranking': 'Error',
                'hand_description': f'Analysis error: {e}',
                'hand_strength': 0,
                'best_five_cards': []
            }
    
    def _analyze_board_texture(self, community_cards: List[str], active_opponents: int = 1) -> Dict:
        """Analyze board texture for draws and dangers with player count consideration."""
        if len(community_cards) < 3:
            return {
                'flush_draw_possible': False,
                'straight_draw_possible': False,
                'paired_board': False,
                'board_wetness': 'Dry',
                'danger_level': 'Low'
            }
        
        # Analyze suits for flush draws
        suits = [card[-1] for card in community_cards]
        suit_counts = {}
        for suit in suits:
            suit_counts[suit] = suit_counts.get(suit, 0) + 1
        
        flush_draw_possible = any(count >= 3 for count in suit_counts.values())
        
        # Analyze ranks for straight draws and pairs
        all_cards = community_cards
        ranks = [self.rank_values[card[:-1]] for card in all_cards]
        ranks.sort()
        straight_draw = self._has_straight_draw(ranks)
        
        # Check for paired board
        rank_counts = {}
        for card in community_cards:
            rank = card[:-1]
            rank_counts[rank] = rank_counts.get(rank, 0) + 1
        
        paired_board = any(count >= 2 for count in rank_counts.values())
        
        # Determine board wetness with player count consideration
        danger_count = 0
        if flush_draw_possible:
            danger_count += 1
        if straight_draw:
            danger_count += 1
        if paired_board:
            danger_count += 1
        
        # Player count multiplier - more players = more dangerous draws
        player_multiplier = 1.0
        if active_opponents >= 7:  # 8+ way pot
            player_multiplier = 2.0  # Very dangerous
        elif active_opponents >= 4:  # 5+ way pot
            player_multiplier = 1.5  # More dangerous
        elif active_opponents >= 2:  # 3+ way pot
            player_multiplier = 1.2  # Slightly more dangerous
        
        effective_danger = danger_count * player_multiplier
        
        if effective_danger >= 3.0:
            wetness = 'Very Wet'
            danger_level = 'Very High'
        elif effective_danger >= 2.0:
            wetness = 'Wet'
            danger_level = 'High'
        elif effective_danger >= 1.0:
            wetness = 'Moderately Wet'
            danger_level = 'Medium'
        else:
            wetness = 'Dry'
            danger_level = 'Low'
        
        # Special warnings for multi-way pots
        warnings = []
        if flush_draw_possible and active_opponents >= 4:
            warnings.append("High flush completion risk with many opponents")
        if straight_draw and active_opponents >= 5:
            warnings.append("Multiple straight possibilities with many players")
        if paired_board and active_opponents >= 3:
            warnings.append("Full house/trips risk in multi-way pot")
        
        return {
            'flush_draw_possible': flush_draw_possible,
            'straight_draw_possible': straight_draw,
            'paired_board': paired_board,
            'board_wetness': wetness,
            'danger_level': danger_level,
            'effective_danger_score': effective_danger,
            'player_count_multiplier': player_multiplier,
            'warnings': warnings
        }
    
    def _has_straight_draw(self, ranks: List[int]) -> bool:
        """Check if there's a potential straight draw on the board."""
        unique_ranks = list(set(ranks))
        unique_ranks.sort()
        
        # Check for 4-card straight potential (needs one more card)
        for i in range(len(unique_ranks) - 3):
            if unique_ranks[i+3] - unique_ranks[i] == 3:
                return True
        
        # Check for A-2-3-4 or A-2-3-K (wheel draw potential)
        if 0 in unique_ranks and 1 in unique_ranks and 2 in unique_ranks and 12 in unique_ranks:
            return True
        
        return False
    
    def _analyze_opponent_possibilities(self, hero_cards: List[str], community_cards: List[str], 
                                     active_opponents: int, known_opponent_cards: List[str] = None) -> Dict:
        """Estimate opponent hand strength distributions."""
        try:
            from poker_engine import HandEvaluator, Card
            
            evaluator = HandEvaluator()
            
            # Convert string cards to Card objects
            def string_to_card(card_str: str):
                return Card.from_string(card_str)
            
            # Calculate remaining deck size accounting for all active players
            # Hero has 2 cards, each active opponent has 2 cards, plus community cards
            known_cards = set(hero_cards + community_cards)
            if known_opponent_cards:
                known_cards.update(known_opponent_cards)
            
            # Calculate cards in opponent hands (2 cards per active opponent)
            opponent_cards_count = active_opponents * 2
            total_known_cards = len(hero_cards) + len(community_cards) + opponent_cards_count
            remaining_deck_size = 52 - total_known_cards
            
            remaining_cards = [card for card in self.full_deck if card not in known_cards]
            
            # Sample opponent hand combinations
            hand_strength_samples = []
            sample_count = min(100, len(remaining_cards) * (len(remaining_cards) - 1) // 2)
            
            import itertools
            opponent_combinations = list(itertools.combinations(remaining_cards, 2))
            random.shuffle(opponent_combinations)
            
            for opponent_cards in opponent_combinations[:sample_count]:
                if len(community_cards) >= 3:  # Only evaluate if we have enough community cards
                    try:
                        opponent_card_objects = [string_to_card(card) for card in opponent_cards]
                        community_card_objects = [string_to_card(card) for card in community_cards]
                        hand_eval = evaluator.evaluate_hand(opponent_card_objects + community_card_objects)
                        hand_strength_samples.append(hand_eval.rank_score)
                    except:
                        continue
            
            if hand_strength_samples:
                avg_strength = sum(hand_strength_samples) / len(hand_strength_samples)
                
                # Count hand type distributions
                hand_combinations = {
                    'High Card': 0,
                    'One Pair': 0,
                    'Two Pair': 0,
                    'Three of a Kind': 0,
                    'Straight': 0,
                    'Flush': 0,
                    'Full House': 0,
                    'Four of a Kind': 0,
                    'Straight Flush': 0,
                    'Royal Flush': 0
                }
                
                # Simplified hand type estimation
                total_combinations = len(remaining_cards) * (len(remaining_cards) - 1) // 2
                hand_combinations['One Pair'] = int(total_combinations * 0.4)
                hand_combinations['High Card'] = int(total_combinations * 0.5)
                hand_combinations['Two Pair'] = int(total_combinations * 0.08)
                hand_combinations['Three of a Kind'] = int(total_combinations * 0.02)
                
                return {
                    'average_hand_strength': avg_strength,
                    'hand_combinations': hand_combinations,
                    'sample_size': len(hand_strength_samples)
                }
            else:
                return {
                    'average_hand_strength': 1000000,  # Default low strength
                    'hand_combinations': {},
                    'sample_size': 0
                }
                
        except Exception as e:
            return {
                'average_hand_strength': 1000000,
                'hand_combinations': {},
                'sample_size': 0,
                'error': str(e)
            }
    
    def _calculate_simple_equity(self, hero_cards: List[str], community_cards: List[str], active_opponents: int) -> Dict:
        """Calculate equity estimation with player-count-aware probabilities."""
        try:
            from poker_engine import HandEvaluator, Card
            
            evaluator = HandEvaluator()
            
            # Convert string cards to Card objects
            def string_to_card(card_str: str):
                return Card.from_string(card_str)
            
            # Calculate remaining deck size accounting for all active players
            opponent_cards_count = active_opponents * 2
            total_known_cards = len(hero_cards) + len(community_cards) + opponent_cards_count
            remaining_deck_size = 52 - total_known_cards
            
            # If we're on the river, we can calculate more precisely
            if len(community_cards) == 5:
                hero_card_objects = [string_to_card(card) for card in hero_cards]
                community_card_objects = [string_to_card(card) for card in community_cards]
                hero_evaluation = evaluator.evaluate_hand(hero_card_objects + community_card_objects)
                
                # Get remaining cards for opponents
                known_cards = set(hero_cards + community_cards)
                remaining_cards = [card for card in self.full_deck if card not in known_cards]
                
                wins = 0
                ties = 0
                losses = 0
                total_simulations = 0
                
                # Sample opponent hands with player-count awareness
                import itertools
                max_simulations = min(200, len(remaining_cards) * (len(remaining_cards) - 1) // 2)
                opponent_combinations = list(itertools.combinations(remaining_cards, 2))
                random.shuffle(opponent_combinations)
                
                # Simulate against each opponent individually, then combine results
                for opponent_cards in opponent_combinations[:max_simulations]:
                    try:
                        opponent_card_objects = [string_to_card(card) for card in opponent_cards]
                        opponent_hand = evaluator.evaluate_hand(opponent_card_objects + community_card_objects)
                        
                        if hero_evaluation.rank_score > opponent_hand.rank_score:
                            wins += 1
                        elif hero_evaluation.rank_score == opponent_hand.rank_score:
                            ties += 1
                        else:
                            losses += 1
                        total_simulations += 1
                    except Exception:
                        continue
                
                if total_simulations > 0:
                    # Adjust win rate based on number of opponents
                    # More opponents = lower win probability even with same hand
                    single_opponent_win_rate = (wins / total_simulations)
                    
                    # Calculate probability of beating ALL opponents
                    # Probability of beating all N opponents = (P(beat one))^N
                    adjusted_win_rate = single_opponent_win_rate ** active_opponents
                    
                    adjusted_tie_rate = (ties / total_simulations) * 0.5  # Ties become less likely with more players
                    adjusted_lose_rate = 1.0 - adjusted_win_rate - adjusted_tie_rate
                    
                    print(f"🎲 Single opponent win rate: {single_opponent_win_rate:.1%}")
                    print(f"🎯 Adjusted for {active_opponents} opponents: {adjusted_win_rate:.1%}")
                    
                    return {
                        'win_percentage': adjusted_win_rate * 100,
                        'tie_percentage': adjusted_tie_rate * 100,
                        'lose_percentage': adjusted_lose_rate * 100,
                        'total_simulations': total_simulations,
                        'single_opponent_win_rate': single_opponent_win_rate * 100
                    }
            
            # For incomplete boards, use player-count-aware estimation
            # Base win rate decreases exponentially with more opponents
            if active_opponents == 1:
                base_win_rate = 45.0  # 1v1 scenarios
            elif active_opponents == 2:
                base_win_rate = 30.0  # 3-way
            elif active_opponents <= 4:
                base_win_rate = 20.0  # 5-way or less
            elif active_opponents <= 6:
                base_win_rate = 15.0  # 7-way or less
            else:
                base_win_rate = 10.0  # 8+ way (very crowded)
            
            # Adjust based on board texture and remaining cards
            if len(community_cards) >= 3:
                # More community cards = more defined probabilities
                base_win_rate *= 1.1
            
            print(f"🎯 Estimated win rate vs {active_opponents} opponents: {base_win_rate:.1f}%")
            
            return {
                'win_percentage': base_win_rate,
                'tie_percentage': 3.0,  # Small tie chance, decreases with more players
                'lose_percentage': 100 - base_win_rate - 3.0,
                'total_simulations': 0,  # Estimated, not simulated
                'player_count_adjustment': f"Adjusted for {active_opponents} active opponents"
            }
            
        except Exception as e:
            # Fallback values
            base_win_rate = 100 / (active_opponents + 1)
            return {
                'win_percentage': base_win_rate,
                'tie_percentage': 5.0,
                'lose_percentage': 100 - base_win_rate - 5.0,
                'total_simulations': 0,
                'error': str(e)
            }
    
    def _calculate_draws(self, hero_cards: List[str], community_cards: List[str]) -> Dict:
        """Calculate drawing possibilities and outs."""
        all_cards = hero_cards + community_cards
        
        # Count suits and ranks
        suits = {}
        ranks = {}
        for card in all_cards:
            suit = card[-1]
            rank = card[:-1]
            suits[suit] = suits.get(suit, 0) + 1
            ranks[rank] = ranks.get(rank, 0) + 1
        
        # Calculate outs (simplified)
        outs = 0
        
        # Flush draw outs
        for suit, count in suits.items():
            if count == 4:  # One card away from flush
                outs += 9  # 13 total suit cards - 4 already seen
        
        # Straight draw outs (simplified - would need more complex analysis)
        # This is a basic estimation
        rank_values = [self.rank_values.get(rank, 0) for rank in ranks.keys()]
        rank_values.sort()
        
        # Check for open-ended straight draw potential
        if len(rank_values) >= 4:
            # Simple check for consecutive ranks
            consecutive_count = 1
            for i in range(1, len(rank_values)):
                if rank_values[i] == rank_values[i-1] + 1:
                    consecutive_count += 1
                else:
                    consecutive_count = 1
            
            if consecutive_count >= 4:
                outs += 8  # Open-ended straight draw
        
        cards_to_come = 5 - len(community_cards)
        if cards_to_come < 0:
            cards_to_come = 0
        
        return {
            'total_outs': outs,
            'cards_to_come': cards_to_come,
            'draw_percentage': (outs * 2 * cards_to_come) if cards_to_come > 0 else 0
        }
