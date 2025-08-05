import React from 'react';
import { Player, Card } from '../types/poker';
import { evaluateHand } from '../utils/handEvaluator';

interface PlayerHandProps {
  player: Player;
  communityCards: Card[];
  isActive: boolean;
  showCards: boolean;
}

const PlayerHand: React.FC<PlayerHandProps> = ({ 
  player, 
  communityCards, 
  isActive, 
  showCards 
}) => {
  const handEvaluation = showCards && player.cards.length === 2 
    ? evaluateHand([...player.cards, ...communityCards])
    : null;

  const getCardDisplay = (card: Card | null, index: number) => {
    if (!card) {
      return (
        <div key={index} className="w-12 h-16 bg-gray-700 border border-gray-600 rounded-lg flex items-center justify-center">
          <span className="text-gray-500 text-xs">?</span>
        </div>
      );
    }

    if (!showCards) {
      return (
        <div key={index} className="w-12 h-16 bg-blue-900 border border-blue-700 rounded-lg flex items-center justify-center">
          <div className="w-8 h-12 bg-blue-800 rounded border border-blue-600"></div>
        </div>
      );
    }

    const suitColor = card.suit === '♥' || card.suit === '♦' ? 'text-red-500' : 'text-black';
    const bgColor = 'bg-white';

    return (
      <div key={index} className={`w-12 h-16 ${bgColor} border border-gray-300 rounded-lg flex flex-col items-center justify-center shadow-md`}>
        <span className={`text-xs font-bold ${suitColor}`}>{card.rank}</span>
        <span className={`text-lg ${suitColor}`}>{card.suit}</span>
      </div>
    );
  };

  return (
    <div className={`bg-slate-800 rounded-lg p-4 border-2 transition-all duration-300 ${
      isActive ? 'border-yellow-400 shadow-lg shadow-yellow-400/20' : 'border-slate-600'
    }`}>
      {/* Player Info */}
      <div className="flex justify-between items-center mb-3">
        <div>
          <h3 className={`font-bold ${isActive ? 'text-yellow-400' : 'text-white'}`}>
            {player.name}
          </h3>
          <p className="text-gray-300 text-sm">
            Chips: ${player.chips.toLocaleString()}
          </p>
        </div>
        {player.currentBet > 0 && (
          <div className="bg-green-600 text-white px-2 py-1 rounded text-sm font-bold">
            Bet: ${player.currentBet}
          </div>
        )}
      </div>

      {/* Cards */}
      <div className="flex gap-2 mb-3">
        {player.cards.length > 0 ? (
          player.cards.map((card, index) => getCardDisplay(card, index))
        ) : (
          <>
            {getCardDisplay(null, 0)}
            {getCardDisplay(null, 1)}
          </>
        )}
      </div>

      {/* Hand Evaluation */}
      {handEvaluation && showCards && (
        <div className="bg-slate-700 rounded p-2">
          <p className="text-xs text-gray-300 mb-1">Hand Strength</p>
          <div className="flex items-center gap-2">
            <div className="flex-1 bg-slate-600 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-red-500 to-green-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${handEvaluation.strength * 100}%` }}
              ></div>
            </div>
            <span className="text-xs text-white font-bold">
              {(handEvaluation.strength * 100).toFixed(0)}%
            </span>
          </div>
          <p className="text-xs text-gray-400 mt-1">{handEvaluation.description}</p>
        </div>
      )}

      {/* Player Status */}
      {!player.isActive && (
        <div className="text-center py-2">
          <span className="text-red-400 font-bold text-sm">FOLDED</span>
        </div>
      )}
    </div>
  );
};

export default PlayerHand;