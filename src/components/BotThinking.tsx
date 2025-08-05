import React, { useEffect, useState } from 'react';
import { BotDecision } from '../types/poker';

interface BotThinkingProps {
  botName: string;
  decision: BotDecision | undefined;
  isThinking: boolean;
}

const BotThinking: React.FC<BotThinkingProps> = ({ botName, decision, isThinking }) => {
  const [dots, setDots] = useState('');

  useEffect(() => {
    if (isThinking) {
      const interval = setInterval(() => {
        setDots(prev => prev.length >= 3 ? '' : prev + '.');
      }, 500);
      return () => clearInterval(interval);
    } else {
      setDots('');
    }
  }, [isThinking]);

  if (!isThinking && !decision) {
    return null;
  }

  return (
    <div className="bg-slate-700 rounded-lg p-4 mb-4 border border-slate-600">
      <h3 className="text-lg font-bold text-purple-400 mb-3">🤖 {botName}</h3>
      
      {isThinking ? (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-purple-500 rounded-full animate-pulse"></div>
            <span className="text-gray-300">Thinking{dots}</span>
          </div>
          
          <div className="bg-slate-800 rounded p-3">
            <div className="space-y-1 text-sm text-gray-400">
              <p>• Analyzing hand strength...</p>
              <p>• Calculating pot odds...</p>
              <p>• Evaluating opponent behavior...</p>
              <p>• Determining optimal strategy...</p>
            </div>
          </div>
        </div>
      ) : decision ? (
        <div className="space-y-3">
          {/* Decision */}
          <div className="bg-slate-800 rounded p-3">
            <div className="flex justify-between items-center mb-2">
              <span className="text-gray-300">Decision:</span>
              <span className={`font-bold text-lg ${
                decision.action === 'raise' ? 'text-green-400' :
                decision.action === 'call' ? 'text-yellow-400' :
                decision.action === 'check' ? 'text-blue-400' :
                'text-red-400'
              }`}>
                {decision.action.toUpperCase()}
                {decision.amount > 0 && ` $${decision.amount}`}
              </span>
            </div>
            
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Confidence:</span>
              <span className="text-white">{(decision.confidence * 100).toFixed(0)}%</span>
            </div>
          </div>

          {/* Analysis */}
          <div className="bg-slate-800 rounded p-3 space-y-2">
            <h4 className="text-sm font-bold text-purple-300">Analysis</h4>
            
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="flex justify-between">
                <span className="text-gray-400">Hand Strength:</span>
                <span className="text-white">{(decision.handStrength * 100).toFixed(0)}%</span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-gray-400">Pot Odds:</span>
                <span className="text-white">{(decision.potOdds * 100).toFixed(1)}%</span>
              </div>
              
              <div className="flex justify-between col-span-2">
                <span className="text-gray-400">Expected Value:</span>
                <span className={`font-bold ${decision.expectedValue >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  ${decision.expectedValue.toFixed(0)}
                </span>
              </div>
            </div>
          </div>

          {/* Reasoning */}
          <div className="bg-slate-800 rounded p-3">
            <h4 className="text-sm font-bold text-purple-300 mb-2">Reasoning</h4>
            <p className="text-gray-300 text-sm">{decision.reasoning}</p>
          </div>
        </div>
      ) : null}
    </div>
  );
};

export default BotThinking;