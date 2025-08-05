import React, { useState } from 'react';
import { PlayerAction } from '../types/poker';

interface ActionButtonsProps {
  availableActions: PlayerAction[];
  currentBet: number;
  playerBet: number;
  playerChips: number;
  onAction: (action: PlayerAction, amount?: number) => void;
  disabled: boolean;
}

const ActionButtons: React.FC<ActionButtonsProps> = ({
  availableActions,
  currentBet,
  playerBet,
  playerChips,
  onAction,
  disabled
}) => {
  const [raiseAmount, setRaiseAmount] = useState(Math.min(100, playerChips));

  const callAmount = currentBet - playerBet;
  const minRaise = Math.max(currentBet * 2, currentBet + 50);
  const maxRaise = playerChips;

  const handleRaise = () => {
    const amount = Math.min(Math.max(raiseAmount, minRaise), maxRaise);
    onAction(PlayerAction.RAISE, amount);
  };

  const getButtonStyle = (action: PlayerAction) => {
    const baseStyle = "px-6 py-3 rounded-lg font-bold text-white transition-all duration-200 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none";
    
    switch (action) {
      case PlayerAction.FOLD:
        return `${baseStyle} bg-red-600 hover:bg-red-700`;
      case PlayerAction.CHECK:
        return `${baseStyle} bg-blue-600 hover:bg-blue-700`;
      case PlayerAction.CALL:
        return `${baseStyle} bg-yellow-600 hover:bg-yellow-700`;
      case PlayerAction.RAISE:
        return `${baseStyle} bg-green-600 hover:bg-green-700`;
      default:
        return `${baseStyle} bg-gray-600 hover:bg-gray-700`;
    }
  };

  const getButtonText = (action: PlayerAction) => {
    switch (action) {
      case PlayerAction.FOLD:
        return "Fold";
      case PlayerAction.CHECK:
        return "Check";
      case PlayerAction.CALL:
        return `Call $${callAmount}`;
      case PlayerAction.RAISE:
        return `Raise $${raiseAmount}`;
      default:
        return action;
    }
  };

  return (
    <div className="space-y-4">
      {/* Action Buttons */}
      <div className="flex gap-3 justify-center flex-wrap">
        {availableActions.map(action => {
          if (action === PlayerAction.RAISE) {
            return (
              <div key={action} className="flex flex-col items-center gap-2">
                <div className="flex items-center gap-2">
                  <input
                    type="range"
                    min={minRaise}
                    max={maxRaise}
                    value={raiseAmount}
                    onChange={(e) => setRaiseAmount(parseInt(e.target.value))}
                    className="w-24"
                    disabled={disabled}
                  />
                  <span className="text-white text-sm w-16">${raiseAmount}</span>
                </div>
                <button
                  onClick={handleRaise}
                  disabled={disabled || !availableActions.includes(action)}
                  className={getButtonStyle(action)}
                >
                  {getButtonText(action)}
                </button>
              </div>
            );
          }

          return (
            <button
              key={action}
              onClick={() => {
                if (action === PlayerAction.CALL) {
                  onAction(action, callAmount);
                } else {
                  onAction(action);
                }
              }}
              disabled={disabled || !availableActions.includes(action)}
              className={getButtonStyle(action)}
            >
              {getButtonText(action)}
            </button>
          );
        })}
      </div>

      {/* Quick Bet Buttons for Raise */}
      {availableActions.includes(PlayerAction.RAISE) && (
        <div className="flex gap-2 justify-center">
          <span className="text-gray-300 text-sm self-center">Quick bets:</span>
          {[
            { label: "1/4 Pot", amount: Math.floor(currentBet * 0.25) },
            { label: "1/2 Pot", amount: Math.floor(currentBet * 0.5) },
            { label: "Pot", amount: currentBet },
            { label: "All-In", amount: playerChips }
          ].map(({ label, amount }) => (
            <button
              key={label}
              onClick={() => setRaiseAmount(Math.min(amount, maxRaise))}
              disabled={disabled}
              className="px-3 py-1 bg-slate-700 hover:bg-slate-600 text-white text-xs rounded transition-colors duration-200"
            >
              {label}
            </button>
          ))}
        </div>
      )}

      {/* Betting Info */}
      <div className="text-center text-gray-400 text-sm space-y-1">
        <p>Current Bet: ${currentBet} | Your Bet: ${playerBet}</p>
        <p>To Call: ${callAmount} | Your Chips: ${playerChips}</p>
        {availableActions.includes(PlayerAction.RAISE) && (
          <p>Min Raise: ${minRaise} | Max Raise: ${maxRaise}</p>
        )}
      </div>
    </div>
  );
};

export default ActionButtons;