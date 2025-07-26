"""
Card Class

Simple representation of a playing card with rank and suit.
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class Card:
    """Represents a playing card with rank and suit."""
    rank: str  # '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A'
    suit: str  # 'h', 'd', 'c', 's' (hearts, diamonds, clubs, spades)
    confidence: float = 0.0
    
    def __str__(self):
        suit_names = {'h': 'Hearts', 'd': 'Diamonds', 'c': 'Clubs', 's': 'Spades'}
        rank_names = {
            '2': 'Two', '3': 'Three', '4': 'Four', '5': 'Five', '6': 'Six',
            '7': 'Seven', '8': 'Eight', '9': 'Nine', 'T': 'Ten',
            'J': 'Jack', 'Q': 'Queen', 'K': 'King', 'A': 'Ace'
        }
        return f"{rank_names.get(self.rank, self.rank)} of {suit_names.get(self.suit, self.suit)}"
