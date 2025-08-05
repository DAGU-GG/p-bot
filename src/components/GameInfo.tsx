import React from 'react';
import { GameState } from '../types/poker';

interface GameInfoProps {
  gameState: GameState;
  winProbability: number;
}

const GameInfo: React.FC<GameInfoProps> = ({ gameState, winProbability }) => {
  const activePlayers = gameState.players.filter(p => p.isActive);
  const currentPlayer = gameState.players[gameState.activePlayerIndex];

  return (
    <div className="bg-slate-800 rounded-lg p-6 space-y-4">
      <h2 className="text-xl font-bold text-white mb-4">🎮 Game Information</h2>
      
      {/* Game Status */}
      <div className="space-y-2">
        <div className="flex justify-between">
          <span className="text-gray-300">Phase:</span>
          <span className="text-white font-bold">{gameState.phase}</span>
        </div>
        
        <div className="flex justify-between">
          <span className="text-gray-300">Pot:</span>
          <span className="text-green-400 font-bold">${gameState.pot.toLocaleString()}</span>
        </div>
        
        <div className="flex justify-between">
          <span className="text-gray-300">Current Bet:</span>
          <span className="text-yellow-400 font-bold">${gameState.currentBet}</span>
        </div>
        
        <div className="flex justify-between">
          <span className="text-gray-300">Active Players:</span>
          <span className="text-white font-bold">{activePlayers.length}</span>
        </div>
      </div>

      {/* Current Player */}
      <div className="border-t border-slate-600 pt-4">
        <h3 className="text-lg font-bold text-yellow-400 mb-2">Current Turn</h3>
        <div className="space-y-2">
          <div className="flex justify-between">
            <span className="text-gray-300">Player:</span>
            <span className="text-white font-bold">{currentPlayer?.name || 'Unknown'}</span>
          </div>
          
          <div className="flex justify-between">
            <span className="text-gray-300">Position:</span>
            <span className="text-white">{currentPlayer?.position || 'N/A'}</span>
          </div>
        </div>
      </div>

      {/* Win Probability */}
      <div className="border-t border-slate-600 pt-4">
        <h3 className="text-lg font-bold text-blue-400 mb-2">Your Hand</h3>
        <div className="space-y-2">
          <div className="flex justify-between">
            <span className="text-gray-300">Win Probability:</span>
            <span className="text-blue-400 font-bold">{(winProbability * 100).toFixed(1)}%</span>
          </div>
          
          <div className="w-full bg-slate-600 rounded-full h-3">
            <div 
              className="bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 h-3 rounded-full transition-all duration-500"
              style={{ width: `${winProbability * 100}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Hand Number */}
      <div className="border-t border-slate-600 pt-4">
        <div className="flex justify-between">
          <span className="text-gray-300">Hand #:</span>
          <span className="text-white font-bold">{gameState.handNumber}</span>
        </div>
      </div>
    </div>
  );
};

export default GameInfo;