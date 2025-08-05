"""
Poker Game Engine
Handles game logic, bot decisions, and hand evaluation.
"""

import random
import time
from typing import List, Optional, Dict, Any
from ..types.poker import *


class GameEngine:
    """Main game engine for poker simulation."""
    
    def __init__(self):
        """Initialize the game engine."""
        self.gameState = None
        self.deck = []
        self.handEvaluator = HandEvaluator()
        self.botAI = BotAI()
        
        # Game settings
        self.smallBlind = 25
        self.bigBlind = 50
        self.startingChips = 2000
        
        # Initialize players
        self.initializePlayers()
    
    def initializePlayers(self):
        """Initialize players for the game."""
        self.players = [
            Player(
                id="human",
                name="You",
                chips=self.startingChips,
                cards=[],
                currentBet=0,
                isBot=False,
                position=0
            ),
            Player(
                id="bot1",
                name="AI Player 1",
                chips=self.startingChips,
                cards=[],
                currentBet=0,
                isBot=True,
                position=1
            ),
            Player(
                id="bot2",
                name="AI Player 2",
                chips=self.startingChips,
                cards=[],
                currentBet=0,
                isBot=True,
                position=2
            )
        ]
    
    def createDeck(self) -> List[Card]:
        """Create a standard 52-card deck."""
        deck = []
        for suit in Suit:
            for rank in Rank:
                deck.append(Card(rank, suit))
        return deck
    
    def shuffleDeck(self):
        """Shuffle the deck."""
        random.shuffle(self.deck)
    
    def dealCards(self):
        """Deal hole cards to all players."""
        for _ in range(2):  # Deal 2 cards to each player
            for player in self.players:
                if player.isActive and self.deck:
                    player.cards.append(self.deck.pop())
    
    def dealCommunityCards(self, count: int):
        """Deal community cards."""
        for _ in range(count):
            if self.deck:
                self.gameState.communityCards.append(self.deck.pop())
    
    def startNewHand(self) -> GameState:
        """Start a new poker hand."""
        # Reset players
        for player in self.players:
            player.cards = []
            player.currentBet = 0
            player.hasActed = False
            player.isActive = player.chips > 0
        
        # Create and shuffle deck
        self.deck = self.createDeck()
        self.shuffleDeck()
        
        # Create new game state
        self.gameState = GameState(
            players=self.players,
            communityCards=[],
            pot=0,
            currentBet=self.bigBlind,
            activePlayerIndex=0,  # Start with first player
            phase=GamePhase.PREFLOP,
            dealerIndex=0,
            smallBlindIndex=1,
            bigBlindIndex=2,
            handNumber=1
        )
        
        # Post blinds
        self.players[1].currentBet = self.smallBlind
        self.players[1].chips -= self.smallBlind
        self.players[2].currentBet = self.bigBlind
        self.players[2].chips -= self.bigBlind
        self.gameState.pot = self.smallBlind + self.bigBlind
        
        # Deal hole cards
        self.dealCards()
        
        return self.gameState
    
    def processPlayerAction(self, action: PlayerAction, amount: int = 0) -> GameState:
        """Process a player action and update game state."""
        currentPlayer = self.players[self.gameState.activePlayerIndex]
        
        if action == PlayerAction.FOLD:
            currentPlayer.isActive = False
        elif action == PlayerAction.CALL:
            callAmount = self.gameState.currentBet - currentPlayer.currentBet
            actualCall = min(callAmount, currentPlayer.chips)
            currentPlayer.currentBet += actualCall
            currentPlayer.chips -= actualCall
            self.gameState.pot += actualCall
        elif action == PlayerAction.RAISE:
            # Calculate raise amount
            callAmount = self.gameState.currentBet - currentPlayer.currentBet
            totalBet = callAmount + amount
            actualBet = min(totalBet, currentPlayer.chips)
            
            currentPlayer.currentBet += actualBet
            currentPlayer.chips -= actualBet
            self.gameState.pot += actualBet
            self.gameState.currentBet = currentPlayer.currentBet
        elif action == PlayerAction.CHECK:
            # No additional betting
            pass
        
        currentPlayer.hasActed = True
        
        # Move to next player
        self.moveToNextPlayer()
        
        # Check if betting round is complete
        if self.isBettingRoundComplete():
            self.advanceToNextPhase()
        
        return self.gameState
    
    def moveToNextPlayer(self):
        """Move to the next active player."""
        originalIndex = self.gameState.activePlayerIndex
        
        while True:
            self.gameState.activePlayerIndex = (self.gameState.activePlayerIndex + 1) % len(self.players)
            
            # Check if we've gone full circle
            if self.gameState.activePlayerIndex == originalIndex:
                break
            
            # Check if this player is active
            if self.players[self.gameState.activePlayerIndex].isActive:
                break
    
    def isBettingRoundComplete(self) -> bool:
        """Check if the current betting round is complete."""
        activePlayers = [p for p in self.players if p.isActive]
        
        if len(activePlayers) <= 1:
            return True
        
        # Check if all active players have acted and have equal bets
        for player in activePlayers:
            if not player.hasActed:
                return False
            if player.currentBet != self.gameState.currentBet and player.chips > 0:
                return False
        
        return True
    
    def advanceToNextPhase(self):
        """Advance to the next game phase."""
        # Reset player actions
        for player in self.players:
            player.hasActed = False
        
        # Reset current bet
        self.gameState.currentBet = 0
        for player in self.players:
            player.currentBet = 0
        
        # Advance phase and deal cards
        if self.gameState.phase == GamePhase.PREFLOP:
            self.gameState.phase = GamePhase.FLOP
            self.dealCommunityCards(3)  # Deal flop
        elif self.gameState.phase == GamePhase.FLOP:
            self.gameState.phase = GamePhase.TURN
            self.dealCommunityCards(1)  # Deal turn
        elif self.gameState.phase == GamePhase.TURN:
            self.gameState.phase = GamePhase.RIVER
            self.dealCommunityCards(1)  # Deal river
        elif self.gameState.phase == GamePhase.RIVER:
            self.gameState.phase = GamePhase.SHOWDOWN
    
    def getGameState(self) -> GameState:
        """Get current game state."""
        return self.gameState
    
    def isGameComplete(self) -> bool:
        """Check if the current hand is complete."""
        if not self.gameState:
            return True
        
        activePlayers = [p for p in self.players if p.isActive]
        
        # Game is complete if only one player remains or we're at showdown
        return len(activePlayers) <= 1 or self.gameState.phase == GamePhase.SHOWDOWN
    
    def getBotDecision(self, bot: Player) -> BotDecision:
        """Get bot decision for current situation."""
        return self.botAI.makeDecision(bot, self.gameState)
    
    def getAvailableActions(self) -> List[PlayerAction]:
        """Get available actions for current player."""
        currentPlayer = self.players[self.gameState.activePlayerIndex]
        actions = []
        
        # Can always fold
        actions.append(PlayerAction.FOLD)
        
        # Can check if no bet to call
        if self.gameState.currentBet == currentPlayer.currentBet:
            actions.append(PlayerAction.CHECK)
        else:
            # Can call if there's a bet
            actions.append(PlayerAction.CALL)
        
        # Can raise if has chips
        if currentPlayer.chips > 0:
            actions.append(PlayerAction.RAISE)
        
        return actions
    
    def getWinProbability(self, playerId: str) -> float:
        """Calculate win probability for a player."""
        player = next((p for p in self.players if p.id == playerId), None)
        if not player or not player.cards:
            return 0.0
        
        # Simple hand strength calculation
        return self.handEvaluator.calculateHandStrength(player.cards, self.gameState.communityCards)


class HandEvaluator:
    """Evaluates poker hands and calculates probabilities."""
    
    def calculateHandStrength(self, holeCards: List[Card], communityCards: List[Card]) -> float:
        """Calculate hand strength (0.0 to 1.0)."""
        if not holeCards or len(holeCards) != 2:
            return 0.0
        
        # Simple hand strength based on hole cards
        card1, card2 = holeCards
        
        # Pocket pairs
        if card1.rank == card2.rank:
            rank_value = self.getRankValue(card1.rank)
            return 0.5 + (rank_value / 26.0)  # 0.5 to 1.0 for pairs
        
        # High cards
        rank1_value = self.getRankValue(card1.rank)
        rank2_value = self.getRankValue(card2.rank)
        avg_rank = (rank1_value + rank2_value) / 2
        
        # Suited bonus
        suited_bonus = 0.1 if card1.suit == card2.suit else 0.0
        
        # Connected bonus
        connected_bonus = 0.05 if abs(rank1_value - rank2_value) == 1 else 0.0
        
        base_strength = avg_rank / 14.0  # Normalize to 0-1
        return min(base_strength + suited_bonus + connected_bonus, 0.95)
    
    def getRankValue(self, rank: Rank) -> int:
        """Get numeric value for rank."""
        rank_values = {
            Rank.TWO: 2, Rank.THREE: 3, Rank.FOUR: 4, Rank.FIVE: 5,
            Rank.SIX: 6, Rank.SEVEN: 7, Rank.EIGHT: 8, Rank.NINE: 9,
            Rank.TEN: 10, Rank.JACK: 11, Rank.QUEEN: 12, Rank.KING: 13, Rank.ACE: 14
        }
        return rank_values.get(rank, 2)


class BotAI:
    """AI system for bot decision making."""
    
    def makeDecision(self, bot: Player, gameState: GameState) -> BotDecision:
        """Make a decision for the bot."""
        # Simple AI logic
        handEvaluator = HandEvaluator()
        handStrength = handEvaluator.calculateHandStrength(bot.cards, gameState.communityCards)
        
        # Calculate pot odds
        potOdds = self.calculatePotOdds(gameState, bot)
        
        # Decision logic
        if handStrength > 0.8:
            action = PlayerAction.RAISE
            amount = min(gameState.pot // 2, bot.chips)
            confidence = 0.9
            reasoning = "Strong hand - aggressive play"
        elif handStrength > 0.6:
            if gameState.currentBet == bot.currentBet:
                action = PlayerAction.CHECK
                amount = 0
            else:
                action = PlayerAction.CALL
                amount = gameState.currentBet - bot.currentBet
            confidence = 0.7
            reasoning = "Good hand - conservative play"
        elif handStrength > 0.4 and potOdds > 0.3:
            action = PlayerAction.CALL
            amount = gameState.currentBet - bot.currentBet
            confidence = 0.5
            reasoning = "Marginal hand with good pot odds"
        else:
            action = PlayerAction.FOLD
            amount = 0
            confidence = 0.8
            reasoning = "Weak hand - fold to preserve chips"
        
        return BotDecision(
            action=action,
            amount=amount,
            confidence=confidence,
            reasoning=reasoning,
            handStrength=handStrength,
            potOdds=potOdds,
            expectedValue=self.calculateExpectedValue(handStrength, potOdds, gameState)
        )
    
    def calculatePotOdds(self, gameState: GameState, player: Player) -> float:
        """Calculate pot odds for the player."""
        betToCall = gameState.currentBet - player.currentBet
        if betToCall <= 0:
            return 1.0
        
        totalPot = gameState.pot + betToCall
        return betToCall / totalPot if totalPot > 0 else 0.0
    
    def calculateExpectedValue(self, handStrength: float, potOdds: float, gameState: GameState) -> float:
        """Calculate expected value of a decision."""
        # Simplified EV calculation
        winProbability = handStrength
        potSize = gameState.pot
        
        return (winProbability * potSize) - ((1 - winProbability) * gameState.currentBet)