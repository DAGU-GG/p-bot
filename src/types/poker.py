"""
Poker Game Types and Interfaces
Defines the data structures used by the React poker game.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class Suit(Enum):
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"
    SPADES = "♠"


class Rank(Enum):
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "T"
    JACK = "J"
    QUEEN = "Q"
    KING = "K"
    ACE = "A"


@dataclass
class Card:
    """Represents a playing card."""
    rank: Rank
    suit: Suit
    
    def __str__(self) -> str:
        return f"{self.rank.value}{self.suit.value}"


@dataclass
class Player:
    """Represents a player in the game."""
    id: str
    name: str
    chips: int
    cards: List[Card]
    currentBet: int
    isBot: bool
    position: int
    isActive: bool = True
    hasActed: bool = False
    
    def __post_init__(self):
        if not self.cards:
            self.cards = []


class GamePhase(Enum):
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"


class PlayerAction(Enum):
    FOLD = "fold"
    CALL = "call"
    RAISE = "raise"
    CHECK = "check"
    ALL_IN = "all_in"


@dataclass
class BotDecision:
    """Represents a bot's decision."""
    action: PlayerAction
    amount: int
    confidence: float
    reasoning: str
    handStrength: float
    potOdds: float
    expectedValue: float


@dataclass
class GameState:
    """Represents the current state of the poker game."""
    players: List[Player]
    communityCards: List[Card]
    pot: int
    currentBet: int
    activePlayerIndex: int
    phase: GamePhase
    dealerIndex: int
    smallBlindIndex: int
    bigBlindIndex: int
    handNumber: int
    
    def __post_init__(self):
        if not self.communityCards:
            self.communityCards = []
        if not self.players:
            self.players = []


@dataclass
class HandEvaluation:
    """Represents hand evaluation results."""
    handType: str
    handRank: int
    kickers: List[Rank]
    description: str
    strength: float  # 0.0 to 1.0


@dataclass
class PotOdds:
    """Represents pot odds calculation."""
    potSize: int
    betToCall: int
    odds: float
    percentage: float
    recommendation: str