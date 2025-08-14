#!/usr/bin/env python3
"""
Poker Engine - Advanced Texas Hold'em Analysis Module

This module serves as the intelligence layer between OCR backend and GUI frontend.
It provides comprehensive poker logic including:
- 52-card deck awareness and tracking
- Hand evaluation and ranking
- Pot odds and equity calculations
- Tournament strategy analysis
- Extensible framework for advanced poker AI

Architecture:
OCR Backend -> Poker Engine -> GUI Frontend
"""

from enum import Enum, IntEnum
from typing import List, Dict, Set, Tuple, Optional, Any
from dataclasses import dataclass
from collections import Counter
import itertools
import json
import time

try:
    from probability_engine import ProbabilityEngine
except ImportError:
    # Fallback if probability engine not available
    ProbabilityEngine = None

class Suit(Enum):
    """Card suits with Unicode symbols."""
    SPADES = "♠"
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"

class Rank(IntEnum):
    """Card ranks with numerical values for comparison."""
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

class HandRank(IntEnum):
    """Poker hand rankings from lowest to highest."""
    HIGH_CARD = 1
    ONE_PAIR = 2
    TWO_PAIR = 3
    THREE_OF_A_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    FOUR_OF_A_KIND = 8
    STRAIGHT_FLUSH = 9
    ROYAL_FLUSH = 10

class GameStage(Enum):
    """Poker game stages."""
    PREFLOP = "Preflop"
    FLOP = "Flop"
    TURN = "Turn"
    RIVER = "River"
    SHOWDOWN = "Showdown"

@dataclass
class Card:
    """Represents a single playing card."""
    rank: Rank
    suit: Suit
    
    def __str__(self):
        return f"{self.rank_symbol()}{self.suit.value}"
    
    def __hash__(self):
        return hash((self.rank, self.suit))
    
    def __eq__(self, other):
        return isinstance(other, Card) and self.rank == other.rank and self.suit == other.suit
    
    def rank_symbol(self):
        """Get the rank symbol (A, K, Q, J, 10, 9, etc.)."""
        if self.rank == Rank.ACE:
            return "A"
        elif self.rank == Rank.KING:
            return "K"
        elif self.rank == Rank.QUEEN:
            return "Q"
        elif self.rank == Rank.JACK:
            return "J"
        else:
            return str(self.rank)
    
    @classmethod
    def from_string(cls, card_str: str) -> 'Card':
        """Create card from string like 'A♠', 'Ks', '10H', etc."""
        if not card_str or len(card_str) < 2:
            raise ValueError(f"Invalid card string: {card_str}")
        
        # Handle different formats
        card_str = card_str.strip().upper()
        
        # Extract suit (last character)
        suit_char = card_str[-1]
        rank_str = card_str[:-1]
        
        # Parse suit
        suit_map = {
            '♠': Suit.SPADES, 'S': Suit.SPADES, 'SPADES': Suit.SPADES,
            '♥': Suit.HEARTS, 'H': Suit.HEARTS, 'HEARTS': Suit.HEARTS,
            '♦': Suit.DIAMONDS, 'D': Suit.DIAMONDS, 'DIAMONDS': Suit.DIAMONDS,
            '♣': Suit.CLUBS, 'C': Suit.CLUBS, 'CLUBS': Suit.CLUBS
        }
        
        if suit_char not in suit_map:
            raise ValueError(f"Invalid suit: {suit_char}")
        suit = suit_map[suit_char]
        
        # Parse rank
        rank_map = {
            'A': Rank.ACE, 'K': Rank.KING, 'Q': Rank.QUEEN, 'J': Rank.JACK,
            '10': Rank.TEN, '9': Rank.NINE, '8': Rank.EIGHT, '7': Rank.SEVEN,
            '6': Rank.SIX, '5': Rank.FIVE, '4': Rank.FOUR, '3': Rank.THREE, '2': Rank.TWO
        }
        
        if rank_str in rank_map:
            rank = rank_map[rank_str]
        else:
            raise ValueError(f"Invalid rank: {rank_str}")
        
        return cls(rank, suit)

@dataclass
class HandEvaluation:
    """Result of hand evaluation."""
    hand_rank: HandRank
    rank_score: int
    tiebreak_tuple: Tuple[int, ...]
    hand_name: str
    best_five_cards: List[Card]
    description: str

@dataclass
class PlayerState:
    """Represents a player's current state."""
    name: str
    position: int
    stack_size: Optional[float]
    hole_cards: List[Card]
    is_active: bool
    is_sitting_out: bool
    has_folded: bool

class PokerDeck:
    """Manages the 52-card deck and tracks visible/unknown cards."""
    
    def __init__(self):
        self.full_deck = self._create_full_deck()
        self.known_cards: Set[Card] = set()
        self.unknown_cards: Set[Card] = set(self.full_deck)
        
    def _create_full_deck(self) -> Set[Card]:
        """Create a complete 52-card deck."""
        deck = set()
        for suit in Suit:
            for rank in Rank:
                deck.add(Card(rank, suit))
        return deck
    
    def add_known_card(self, card: Card):
        """Mark a card as known/visible."""
        if card in self.full_deck:
            self.known_cards.add(card)
            self.unknown_cards.discard(card)
    
    def add_known_cards(self, cards: List[Card]):
        """Mark multiple cards as known."""
        for card in cards:
            self.add_known_card(card)
    
    def reset(self):
        """Reset deck to full unknown state."""
        self.known_cards.clear()
        self.unknown_cards = set(self.full_deck)
    
    def get_remaining_count(self) -> int:
        """Get number of unknown cards remaining."""
        return len(self.unknown_cards)
    
    def get_known_count(self) -> int:
        """Get number of known cards."""
        return len(self.known_cards)

class HandEvaluator:
    """Evaluates poker hands and determines rankings."""
    
    @staticmethod
    def evaluate_hand(cards: List[Card]) -> HandEvaluation:
        """Evaluate the best 5-card hand from up to 7 cards."""
        if len(cards) < 5:
            raise ValueError("Need at least 5 cards to evaluate a hand")
        
        if len(cards) == 5:
            best_hand = cards
        else:
            # Find best 5-card combination from 6 or 7 cards
            best_hand = None
            best_evaluation = None
            
            for combo in itertools.combinations(cards, 5):
                evaluation = HandEvaluator._evaluate_five_cards(list(combo))
                if best_evaluation is None or HandEvaluator._is_better_hand(evaluation, best_evaluation):
                    best_evaluation = evaluation
                    best_hand = list(combo)
            
            return best_evaluation
        
        return HandEvaluator._evaluate_five_cards(best_hand)
    
    @staticmethod
    def _evaluate_five_cards(cards: List[Card]) -> HandEvaluation:
        """Evaluate exactly 5 cards."""
        if len(cards) != 5:
            raise ValueError("Must evaluate exactly 5 cards")
        
        # Sort cards by rank (high to low)
        sorted_cards = sorted(cards, key=lambda c: c.rank, reverse=True)
        ranks = [card.rank for card in sorted_cards]
        suits = [card.suit for card in sorted_cards]
        
        # Check for flush
        is_flush = len(set(suits)) == 1
        
        # Check for straight
        is_straight, straight_high = HandEvaluator._check_straight(ranks)
        
        # Count rank occurrences
        rank_counts = Counter(ranks)
        count_values = sorted(rank_counts.values(), reverse=True)
        
        # Determine hand type
        if is_straight and is_flush:
            if ranks[0] == Rank.ACE and ranks[1] == Rank.KING:
                return HandEvaluation(
                    HandRank.ROYAL_FLUSH,
                    10000,
                    (10, Rank.ACE),
                    "Royal Flush",
                    sorted_cards,
                    f"Royal Flush in {suits[0].value}"
                )
            else:
                return HandEvaluation(
                    HandRank.STRAIGHT_FLUSH,
                    9000 + straight_high,
                    (9, straight_high),
                    "Straight Flush",
                    sorted_cards,
                    f"Straight Flush, {Card(straight_high, suits[0]).rank_symbol()} high"
                )
        
        elif count_values == [4, 1]:  # Four of a kind
            quads_rank = max(rank_counts, key=rank_counts.get)
            kicker = min(rank_counts, key=rank_counts.get)
            return HandEvaluation(
                HandRank.FOUR_OF_A_KIND,
                8000 + quads_rank * 100 + kicker,
                (8, quads_rank, kicker),
                "Four of a Kind",
                sorted_cards,
                f"Four {Card(quads_rank, Suit.SPADES).rank_symbol()}s"
            )
        
        elif count_values == [3, 2]:  # Full house
            trips_rank = max(rank_counts, key=rank_counts.get)
            pair_rank = min(rank_counts, key=rank_counts.get)
            return HandEvaluation(
                HandRank.FULL_HOUSE,
                7000 + trips_rank * 100 + pair_rank,
                (7, trips_rank, pair_rank),
                "Full House",
                sorted_cards,
                f"Full House, {Card(trips_rank, Suit.SPADES).rank_symbol()}s over {Card(pair_rank, Suit.SPADES).rank_symbol()}s"
            )
        
        elif is_flush:
            return HandEvaluation(
                HandRank.FLUSH,
                6000 + sum(rank * (15 ** (4-i)) for i, rank in enumerate(ranks)),
                (6, *ranks),
                "Flush",
                sorted_cards,
                f"Flush, {Card(ranks[0], suits[0]).rank_symbol()} high"
            )
        
        elif is_straight:
            return HandEvaluation(
                HandRank.STRAIGHT,
                5000 + straight_high,
                (5, straight_high),
                "Straight",
                sorted_cards,
                f"Straight, {Card(straight_high, Suit.SPADES).rank_symbol()} high"
            )
        
        elif count_values == [3, 1, 1]:  # Three of a kind
            trips_rank = max(rank_counts, key=rank_counts.get)
            kickers = sorted([r for r in ranks if rank_counts[r] == 1], reverse=True)
            return HandEvaluation(
                HandRank.THREE_OF_A_KIND,
                4000 + trips_rank * 10000 + kickers[0] * 100 + kickers[1],
                (4, trips_rank, *kickers),
                "Three of a Kind",
                sorted_cards,
                f"Three {Card(trips_rank, Suit.SPADES).rank_symbol()}s"
            )
        
        elif count_values == [2, 2, 1]:  # Two pair
            pairs = sorted([r for r in ranks if rank_counts[r] == 2], reverse=True)
            kicker = [r for r in ranks if rank_counts[r] == 1][0]
            return HandEvaluation(
                HandRank.TWO_PAIR,
                3000 + pairs[0] * 10000 + pairs[1] * 100 + kicker,
                (3, pairs[0], pairs[1], kicker),
                "Two Pair",
                sorted_cards,
                f"Two Pair, {Card(pairs[0], Suit.SPADES).rank_symbol()}s and {Card(pairs[1], Suit.SPADES).rank_symbol()}s"
            )
        
        elif count_values == [2, 1, 1, 1]:  # One pair
            pair_rank = max(rank_counts, key=rank_counts.get)
            kickers = sorted([r for r in ranks if rank_counts[r] == 1], reverse=True)
            return HandEvaluation(
                HandRank.ONE_PAIR,
                2000 + pair_rank * 1000000 + sum(k * (15 ** (2-i)) for i, k in enumerate(kickers)),
                (2, pair_rank, *kickers),
                "One Pair",
                sorted_cards,
                f"Pair of {Card(pair_rank, Suit.SPADES).rank_symbol()}s"
            )
        
        else:  # High card
            return HandEvaluation(
                HandRank.HIGH_CARD,
                1000 + sum(rank * (15 ** (4-i)) for i, rank in enumerate(ranks)),
                (1, *ranks),
                "High Card",
                sorted_cards,
                f"{Card(ranks[0], suits[0]).rank_symbol()} high"
            )
    
    @staticmethod
    def _check_straight(ranks: List[int]) -> Tuple[bool, int]:
        """Check if ranks form a straight. Returns (is_straight, high_card)."""
        unique_ranks = sorted(set(ranks), reverse=True)
        
        if len(unique_ranks) < 5:
            return False, 0
        
        # Check for normal straight
        for i in range(len(unique_ranks) - 4):
            if unique_ranks[i] - unique_ranks[i+4] == 4:
                return True, unique_ranks[i]
        
        # Check for A-2-3-4-5 straight (wheel)
        if set(unique_ranks[:4]) == {Rank.ACE, Rank.FIVE, Rank.FOUR, Rank.THREE, Rank.TWO}:
            return True, Rank.FIVE
        
        return False, 0
    
    @staticmethod
    def _is_better_hand(hand1: HandEvaluation, hand2: HandEvaluation) -> bool:
        """Compare two hand evaluations. Returns True if hand1 is better."""
        return hand1.rank_score > hand2.rank_score

class PokerEngine:
    """Main poker engine that processes OCR data and provides poker intelligence."""
    
    def __init__(self):
        self.deck = PokerDeck()
        self.players: Dict[str, PlayerState] = {}
        self.community_cards: List[Card] = []
        self.pot_size: Optional[float] = None
        self.current_stage: GameStage = GameStage.PREFLOP
        self.hero_name: str = "Hero"
        self.active_players_count: int = 0
        
        # Analysis results
        self.hero_hand_evaluation: Optional[HandEvaluation] = None
        self.analysis_timestamp: float = 0
        
        # Initialize probability engine
        self.probability_engine = ProbabilityEngine() if ProbabilityEngine else None
        
    def process_ocr_data(self, ocr_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing function that takes OCR results and returns enhanced poker analysis.
        
        Args:
            ocr_results: Raw OCR data from SimplePokerBot
            
        Returns:
            Enhanced analysis with poker intelligence
        """
        start_time = time.time()
        
        # Reset deck for new analysis
        self.deck.reset()
        
        # Process hero cards
        hero_cards = self._parse_cards(ocr_results.get('hero_cards', []))
        if hero_cards:
            self.players[self.hero_name] = PlayerState(
                name=self.hero_name,
                position=0,
                stack_size=None,
                hole_cards=hero_cards,
                is_active=True,
                is_sitting_out=False,
                has_folded=False
            )
            self.deck.add_known_cards(hero_cards)
        
        # Process community cards
        self.community_cards = self._parse_cards(ocr_results.get('community_cards', []))
        if self.community_cards:
            self.deck.add_known_cards(self.community_cards)
        
        # Determine game stage
        self.current_stage = self._determine_stage(len(self.community_cards))
        
        # Process pot size
        self.pot_size = self._parse_pot_size(ocr_results.get('pot', ''))
        
        # Process tournament data if available
        self._process_tournament_data(ocr_results)
        
        # Evaluate hero's hand if possible
        if hero_cards and len(hero_cards) == 2:
            all_cards = hero_cards + self.community_cards
            if len(all_cards) >= 5:
                self.hero_hand_evaluation = HandEvaluator.evaluate_hand(all_cards)
            elif len(all_cards) == 2:  # Preflop
                self.hero_hand_evaluation = self._evaluate_preflop_hand(hero_cards)
        
        # Calculate remaining deck information based on players actually in the hand
        seated_players = self._count_seated_players(ocr_results)
        sitting_out_players = self._count_sitting_out_players(ocr_results)
        active_seated_players = seated_players - sitting_out_players
        
        print(f"🔍 DEBUG: seated_players={seated_players}, sitting_out={sitting_out_players}, active_seated={active_seated_players}")
        
        # Calculate cards accounted for
        hero_cards_count = len([c for c in hero_cards if c]) if hero_cards else 0
        community_cards_count = len(self.community_cards)
        
        # Deck calculation: 52 - community - (2 × active seated players who were dealt cards)
        cards_dealt_to_active = active_seated_players * 2  # All active seated players
        remaining_deck_size = 52 - community_cards_count - cards_dealt_to_active
        
        processing_time = (time.time() - start_time) * 1000
        
        # Build enhanced analysis
        enhanced_analysis = {
            # Original OCR data
            'ocr_results': ocr_results,
            
            # Poker engine analysis
            'poker_analysis': {
                'stage': self.current_stage.value,
                'hero_cards': [str(card) for card in hero_cards] if hero_cards else [],
                'community_cards': [str(card) for card in self.community_cards],
                'pot_size': self.pot_size,
                'hero_hand_evaluation': self._serialize_hand_evaluation(self.hero_hand_evaluation),
                
                # Deck analysis
                'deck_analysis': {
                    'known_cards': len(self.deck.known_cards),
                    'unknown_cards': len(self.deck.unknown_cards),
                    'hero_cards': hero_cards_count,
                    'community_cards': community_cards_count,
                    'seated_players': seated_players + 1,  # Include hero in total seated count for GUI
                    'sitting_out_players': sitting_out_players,
                    'active_seated_players': seated_players + 1 - sitting_out_players,  # Total seated minus sitting out players (including hero)
                    'cards_dealt_to_active': cards_dealt_to_active,
                    'remaining_deck_size': remaining_deck_size,
                    'estimated_active_players': self._estimate_active_players(ocr_results),
                    'tournament_analysis': ocr_results.get('tournament_analysis', {})
                },
                
                # Performance
                'processing_time_ms': processing_time,
                'analysis_timestamp': time.time()
            },
            
            # Probability analysis
            'probability_analysis': self._calculate_probability_analysis(hero_cards, ocr_results),
            
            # GUI display data
            'gui_display': self._create_gui_display_data(self._calculate_probability_analysis(hero_cards, ocr_results))
        }
        
        return enhanced_analysis
    
    def _parse_cards(self, card_strings: List[str]) -> List[Card]:
        """Parse card strings into Card objects."""
        cards = []
        for card_str in card_strings:
            if card_str and card_str.strip():
                try:
                    card = Card.from_string(card_str.strip())
                    cards.append(card)
                except ValueError as e:
                    print(f"⚠️ Failed to parse card '{card_str}': {e}")
        return cards
    
    def _determine_stage(self, community_count: int) -> GameStage:
        """Determine game stage based on community cards."""
        if community_count == 0:
            return GameStage.PREFLOP
        elif community_count == 3:
            return GameStage.FLOP
        elif community_count == 4:
            return GameStage.TURN
        elif community_count == 5:
            return GameStage.RIVER
        else:
            return GameStage.PREFLOP
    
    def _parse_pot_size(self, pot_str: str) -> Optional[float]:
        """Parse pot size string into float."""
        if not pot_str:
            return None
        
        try:
            # Remove currency symbols and parse
            clean_pot = pot_str.replace('$', '').replace(',', '').strip()
            return float(clean_pot)
        except ValueError:
            return None
    
    def _process_tournament_data(self, ocr_results: Dict[str, Any]):
        """Process tournament-specific data like stack sizes and player states."""
        tournament_data = ocr_results.get('tournament_data', {})
        if not tournament_data:
            self.active_players_count = self._estimate_active_players(ocr_results)
            return
            
        # Analyze tournament state
        analysis = self._analyze_tournament_state(tournament_data)
        ocr_results['tournament_analysis'] = analysis
        self.active_players_count = analysis.get('active_in_hand', self._estimate_active_players(ocr_results))
    
    def _analyze_tournament_state(self, tournament_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze tournament state and provide detailed player breakdown."""
        print(f"🔍 TOURNAMENT ANALYSIS DEBUG: tournament_data keys = {list(tournament_data.keys())}")
        
        analysis = {
            'total_seats': 9,  # Fixed: Should be 9 for 9-max tables
            'players_present': 0,
            'sitting_out': 0,
            'active_stacks': [],
            'player_details': [],
            'active_in_hand': 0
        }
        
        for position in range(1, 10):  # Fixed: Should be 1-9 for 9-max tables
            player_name = tournament_data.get(f'Position_{position}_name', '')
            player_stack = tournament_data.get(f'Position_{position}_stack', '')
            
            print(f"🔍 TOURNAMENT Position_{position}: name='{player_name}', stack='{player_stack}'")
            
            if player_name and player_name.strip():
                analysis['players_present'] += 1
                
                player_info = {
                    'position': position,
                    'name': player_name,
                    'stack': player_stack,
                    'status': 'active'
                }
                
                # Check for sitting out indicators based on "Sitting Out" text or empty stack
                if ('sitting' in player_stack.lower() and 'out' in player_stack.lower()) or \
                   ('sitting' in player_name.lower() and 'out' in player_name.lower()) or \
                   (player_name and player_name.strip() and not player_stack.strip()) or \
                   any(keyword in player_name.lower() for keyword in ['away', 'afk']):
                    analysis['sitting_out'] += 1
                    player_info['status'] = 'sitting_out'
                    print(f"🔍 FOUND SITTING OUT: Position_{position} - {player_name} (empty stack: {not player_stack.strip()})")
                else:
                    # Check for known active players (LEAO, Jonnio00)
                    if any(name in player_name.lower() for name in ['leao', 'jonnio']):
                        analysis['active_in_hand'] += 1
                        player_info['status'] = 'active_in_hand'
                    elif player_stack:
                        analysis['active_stacks'].append(player_stack)
                        analysis['active_in_hand'] += 1
                        player_info['status'] = 'likely_active'
                
                analysis['player_details'].append(player_info)
        
        # Add hero to active count if we have hero cards
        analysis['active_in_hand'] += 1  # Hero is always counted if we see their cards
        
        return analysis
    
    def _calculate_probability_analysis(self, hero_cards: List[Card], ocr_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Calculate probability analysis using the probability engine."""
        if not self.probability_engine or not hero_cards or len(hero_cards) != 2:
            return None
            
        try:
            # Convert Card objects to strings
            hero_card_strings = [str(card) for card in hero_cards]
            community_card_strings = [str(card) for card in self.community_cards]
            
            # Calculate active seated players for deck size
            seated_players = self._count_seated_players(ocr_results)
            sitting_out_players = self._count_sitting_out_players(ocr_results)
            active_seated_players = seated_players - sitting_out_players
            
            return self.probability_engine.calculate_hand_probabilities(
                hero_cards=hero_card_strings,
                community_cards=community_card_strings,
                active_opponents=max(1, self.active_players_count - 1),  # Opponents in betting round
                total_active_players=active_seated_players  # All active seated players for deck calculation
            )
        except Exception as e:
            print(f"⚠️ Probability analysis error: {e}")
            return None
    
    def _estimate_active_players(self, ocr_results: Dict[str, Any]) -> int:
        """Estimate number of active players based on available data and opponent card detection."""
        # First check if we have opponent card detection data (most accurate)
        opponent_card_data = ocr_results.get('opponent_cards', {})
        if opponent_card_data and opponent_card_data.get('total_active_players'):
            active_count = opponent_card_data['total_active_players']
            print(f"🎯 Using opponent card detection: {active_count} active players")
            return active_count
        
        # Fallback to tournament data analysis
        community_cards = len([c for c in ocr_results.get('community_cards', []) if c and c != 'Unknown'])
        tournament_data = ocr_results.get('tournament_data', {})
        
        if tournament_data:
            total_players = 0
            sitting_out = 0
            
            # Count players from tournament data (8-max)
            for position in range(1, 9):
                player_name = tournament_data.get(f'Position_{position}_name', '')
                player_stack = tournament_data.get(f'Position_{position}_stack', '')
                
                if player_name and player_name.strip() and player_stack:
                    player_stack = tournament_data.get(f'Position_{position}_stack', '')
                    
                    total_players += 1
                    
                    # Check if sitting out based on "Sitting Out" text or empty stack
                    if ('sitting' in player_stack.lower() and 'out' in player_stack.lower()) or \
                       ('sitting' in player_name.lower() and 'out' in player_name.lower()) or \
                       (player_name and player_name.strip() and not player_stack.strip()) or \
                       any(keyword in player_name.lower() for keyword in ['away', 'afk']):
                        sitting_out += 1
            
            # Estimate based on game stage
            if community_cards == 5:  # River - typically 2-3 players
                return max(2, min(3, total_players - sitting_out))
            elif community_cards >= 3:  # Flop/Turn - typically 3-4 players
                return max(3, min(4, total_players - sitting_out))
            else:  # Pre-flop - more players
                return max(4, total_players - sitting_out)
        
        # Final fallback based on community cards stage only
        stage_estimates = {
            0: 6,  # Pre-flop: most players still in
            3: 4,  # Flop: some have folded
            4: 3,  # Turn: fewer players
            5: 3   # River: even fewer players
        }
        
        return stage_estimates.get(community_cards, 6)
    
    def _count_seated_players(self, ocr_results: Dict[str, Any]) -> int:
        """Count total players seated at the table (excluding hero, including sitting out)."""
        tournament_data = ocr_results.get('tournament_data', {})
        if not tournament_data:
            return 8  # Default for 8-max table
        
        seated_count = 0
        for position in range(1, 10):  # Check positions 1-9 for 9-max
            player_name = tournament_data.get(f'Position_{position}_name', '')
            player_stack = tournament_data.get(f'Position_{position}_stack', '')
            
            # Player is seated if they have a name (stack can be empty if sitting out)
            if player_name and player_name.strip():
                seated_count += 1
                print(f"🔍 Found seated player: Position_{position} - {player_name} (stack: '{player_stack}')")
            
        return seated_count
    
    def _count_sitting_out_players(self, ocr_results: Dict[str, Any]) -> int:
        """Count players who are sitting out based on 'Sitting Out' text, empty stacks, or sitting out indicators."""
        tournament_data = ocr_results.get('tournament_data', {})
        if not tournament_data:
            return 0
        
        print(f"🔍 SITTING OUT DEBUG: tournament_data keys = {list(tournament_data.keys())}")
        
        sitting_out_count = 0
        for position in range(1, 10):  # Check positions 1-9 for 9-max
            player_name = tournament_data.get(f'Position_{position}_name', '')
            player_stack = tournament_data.get(f'Position_{position}_stack', '')
            
            print(f"🔍 Position_{position}: name='{player_name}', stack='{player_stack}'")
            
            # Check for explicit "Sitting Out" text in stack area
            if 'sitting' in player_stack.lower() and 'out' in player_stack.lower():
                sitting_out_count += 1
                print(f"🔍 Found sitting out player (text in stack): Position_{position} - {player_name} ({player_stack})")
            # Check for "Sitting Out" text in name area
            elif 'sitting' in player_name.lower() and 'out' in player_name.lower():
                sitting_out_count += 1
                print(f"🔍 Found sitting out player (text in name): Position_{position} - {player_name}")
            # Player is sitting out if they have a name but no stack (empty stack OCR)
            elif player_name and player_name.strip() and not player_stack.strip():
                sitting_out_count += 1
                print(f"🔍 Found sitting out player (empty stack): Position_{position} - {player_name}")
            # Also check for other sitting out keywords
            elif player_name and any(keyword in player_name.lower() for keyword in ['away', 'afk']):
                sitting_out_count += 1
                print(f"🔍 Found sitting out player (away): Position_{position} - {player_name}")
        
        print(f"🔍 SITTING OUT TOTAL: {sitting_out_count}")
        return sitting_out_count
    
    def _evaluate_preflop_hand(self, hole_cards: List[Card]) -> HandEvaluation:
        """Evaluate preflop hand strength."""
        if len(hole_cards) != 2:
            raise ValueError("Preflop evaluation requires exactly 2 cards")
        
        card1, card2 = hole_cards
        high_card = max(card1.rank, card2.rank)
        low_card = min(card1.rank, card2.rank)
        
        # Check for pair
        if card1.rank == card2.rank:
            description = f"Pocket {card1.rank_symbol()}s"
            rank_score = 2000 + card1.rank * 100
            return HandEvaluation(
                HandRank.ONE_PAIR,
                rank_score,
                (2, card1.rank),
                "Pocket Pair",
                hole_cards,
                description
            )
        
        # Check for suited
        suited = card1.suit == card2.suit
        suited_bonus = 50 if suited else 0
        
        # High card hand
        rank_score = 1000 + high_card * 15 + low_card + suited_bonus
        description = f"{Card(high_card, card1.suit).rank_symbol()}{Card(low_card, card2.suit).rank_symbol()}"
        if suited:
            description += " suited"
        else:
            description += " offsuit"
        
        return HandEvaluation(
            HandRank.HIGH_CARD,
            rank_score,
            (1, high_card, low_card),
            "High Card",
            hole_cards,
            description
        )
    
    def _serialize_hand_evaluation(self, evaluation: Optional[HandEvaluation]) -> Optional[Dict[str, Any]]:
        """Convert HandEvaluation to JSON-serializable format."""
        if not evaluation:
            return None
        
        return {
            'hand_rank': evaluation.hand_rank.name,
            'hand_rank_value': evaluation.hand_rank.value,
            'rank_score': evaluation.rank_score,
            'tiebreak_tuple': list(evaluation.tiebreak_tuple),
            'hand_name': evaluation.hand_name,
            'best_five_cards': [str(card) for card in evaluation.best_five_cards],
            'description': evaluation.description
        }
    
    def _create_gui_display_data(self, probability_analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create formatted data for GUI display."""
        display_data = {
            'stage_display': f"🎯 Stage: {self.current_stage.value}",
            'pot_display': f"💰 Pot: ${self.pot_size:.2f}" if self.pot_size else "💰 Pot: Unknown",
            'deck_status': f"🃏 Deck: {self.deck.get_known_count()} known, {self.deck.get_remaining_count()} unknown",
        }
        
        # Hero hand display
        if self.hero_hand_evaluation:
            eval_data = self.hero_hand_evaluation
            display_data['hero_hand_display'] = f"🎲 Hand: {eval_data.hand_name} - {eval_data.description}"
            display_data['hero_hand_strength'] = f"💪 Strength: {eval_data.rank_score}"
        else:
            display_data['hero_hand_display'] = "🎲 Hand: Not evaluated"
            display_data['hero_hand_strength'] = "💪 Strength: Unknown"
        
        # Add probability analysis display
        if probability_analysis and 'equity' in probability_analysis:
            equity = probability_analysis['equity']
            display_data['equity_display'] = f"📊 Win: {equity['win_percentage']:.1f}% | Tie: {equity['tie_percentage']:.1f}% | Lose: {equity['lose_percentage']:.1f}%"
        
        if probability_analysis and 'opponent_analysis' in probability_analysis:
            opp_analysis = probability_analysis['opponent_analysis']
            if 'average_hand_strength' in opp_analysis:
                avg_strength = opp_analysis['average_hand_strength']
                display_data['opponent_strength'] = f"🎯 Opponents Avg: {avg_strength:.3f}"
        
        if probability_analysis and 'board_texture' in probability_analysis:
            texture = probability_analysis['board_texture']
            draws = []
            if texture.get('flush_draw_possible'): draws.append("Flush")
            if texture.get('straight_draw_possible'): draws.append("Straight")
            if draws:
                display_data['draw_analysis'] = f"⚠️ Draws: {', '.join(draws)}"
        
        return display_data

def test_poker_engine():
    """Test the poker engine with sample data."""
    print("🧪 Testing Poker Engine...")
    
    engine = PokerEngine()
    
    # Test data mimicking OCR results
    test_ocr_results = {
        'hero_cards': ['8♠', '4♥'],
        'community_cards': ['K♣', '4♣', 'A♥', '5♦', '7♦'],
        'pot': '52.20',
        'stage': 'River',
        'estimated_players': 6
    }
    
    print(f"📊 Test OCR Input: {test_ocr_results}")
    
    # Process through engine
    analysis = engine.process_ocr_data(test_ocr_results)
    
    print("\n🔍 Poker Engine Analysis:")
    poker_analysis = analysis['poker_analysis']
    
    print(f"   Stage: {poker_analysis['stage']}")
    print(f"   Hero Cards: {poker_analysis['hero_cards']}")
    print(f"   Community: {poker_analysis['community_cards']}")
    print(f"   Pot: ${poker_analysis['pot_size']}")
    
    if poker_analysis['hero_hand_evaluation']:
        hand_eval = poker_analysis['hero_hand_evaluation']
        print(f"   Hero Hand: {hand_eval['hand_name']} - {hand_eval['description']}")
        print(f"   Hand Strength: {hand_eval['rank_score']}")
    
    deck_analysis = poker_analysis['deck_analysis']
    print(f"\n🃏 Deck Analysis:")
    print(f"   Known Cards: {deck_analysis['known_cards']}")
    print(f"   Unknown Cards: {deck_analysis['unknown_cards']}")
    print(f"   Estimated Active Players: {deck_analysis['estimated_active_players']}")
    print(f"   Remaining Deck Size: {deck_analysis['remaining_deck_size']}")
    
    print(f"\n📱 GUI Display:")
    gui_display = analysis['gui_display']
    for key, value in gui_display.items():
        print(f"   {value}")
    
    print(f"\n⚡ Processing Time: {poker_analysis['processing_time_ms']:.2f}ms")
    print("✅ Poker Engine Test Complete!")

if __name__ == "__main__":
    test_poker_engine()
