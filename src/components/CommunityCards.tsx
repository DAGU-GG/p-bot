import React from 'react';
import { Card, GamePhase } from '../types/poker';

interface CommunityCardsProps {
  cards: Card[];
  phase: GamePhase;
}

const CommunityCards: React.FC<CommunityCardsProps> = ({ cards, phase }) => {
  const getCardDisplay = (card: Card | null, index: number, isRevealed: boolean) => {
    if (!card || !isRevealed) {
      return (
        <div key={index} className="w-16 h-24 bg-gray-700 border border-gray-600 rounded-lg flex items-center justify-center">
          <span className="text-gray-500">?</span>
        </div>
      );
    }

    const suitColor = card.suit === '♥' || card.suit === '♦' ? 'text-red-500' : 'text-black';

    return (
      <div key={index} className="w-16 h-24 bg-white border border-gray-300 rounded-lg flex flex-col items-center justify-center shadow-lg transform hover:scale-105 transition-transform duration-200">
        <span className={`text-sm font-bold ${suitColor}`}>{card.rank}</span>
        <span className={`text-2xl ${suitColor}`}>{card.suit}</span>
      </div>
    );
  };

  const getPhaseDisplay = () => {
    switch (phase) {
      case GamePhase.PREFLOP:
        return "Pre-Flop";
      case GamePhase.FLOP:
        return "Flop";
      case GamePhase.TURN:
        return "Turn";
      case GamePhase.RIVER:
        return "River";
      case GamePhase.SHOWDOWN:
        return "Showdown";
      default:
        return "Unknown";
    }
  };

  const getRevealedCount = () => {
    switch (phase) {
      case GamePhase.PREFLOP:
        return 0;
      case GamePhase.FLOP:
        return 3;
      case GamePhase.TURN:
        return 4;
      case GamePhase.RIVER:
      case GamePhase.SHOWDOWN:
        return 5;
      default:
        return 0;
    }
  };

  const revealedCount = getRevealedCount();

  return (
    <div className="text-center">
      <h2 className="text-2xl font-bold text-white mb-4">{getPhaseDisplay()}</h2>
      
      <div className="flex justify-center gap-3 mb-4">
        {[0, 1, 2, 3, 4].map(index => {
          const card = cards[index] || null;
          const isRevealed = index < revealedCount;
          return getCardDisplay(card, index, isRevealed);
        })}
      </div>

      {cards.length > 0 && (
        <div className="text-gray-300 text-sm">
          {revealedCount} of 5 cards revealed
        </div>
      )}
    </div>
  );
};

export default CommunityCards;