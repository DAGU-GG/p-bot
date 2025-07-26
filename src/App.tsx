import { useState } from 'react';
import { GameEngine } from './utils/gameEngine';
import { GameState, PlayerAction, BotDecision, Player } from './types/poker';
import PlayerHand from './components/PlayerHand';
import CommunityCards from './components/CommunityCards';
import ActionButtons from './components/ActionButtons';
import GameInfo from './components/GameInfo';
import BotThinking from './components/BotThinking';

function App() {
  const [gameEngine] = useState(() => new GameEngine());
  const [gameState, setGameState] = useState<GameState>(gameEngine.getGameState());
  const [isProcessing, setIsProcessing] = useState(false);
  const [botDecisions, setBotDecisions] = useState<Map<string, BotDecision>>(new Map());
  const [gameStarted, setGameStarted] = useState(false);

  const startNewGame = () => {
    const newState = gameEngine.startNewHand();
    setGameState(newState);
    setGameStarted(true);
    setBotDecisions(new Map());
    
    // If first player is bot, process their action
    if (newState.players[newState.activePlayerIndex].isBot) {
      setTimeout(() => processBotTurn(), 1000);
    }
  };

  const handlePlayerAction = async (action: PlayerAction, amount?: number) => {
    if (isProcessing) return;
    
    setIsProcessing(true);
    
    try {
      const newState = gameEngine.processPlayerAction(action, amount || 0);
      setGameState(newState);
      
      // Process bot turns
      setTimeout(() => processBotTurn(), 500);
    } catch (error) {
      console.error('Error processing action:', error);
      setIsProcessing(false);
    }
  };

  const processBotTurn = async () => {
    let currentState = gameEngine.getGameState();
    
    while (currentState.players[currentState.activePlayerIndex].isBot && !gameEngine.isGameComplete()) {
      const currentBot = currentState.players[currentState.activePlayerIndex];
      
      // Show bot thinking
      setIsProcessing(true);
      
      // Get bot decision
      const decision = gameEngine.getBotDecision(currentBot);
      setBotDecisions((prev: Map<string, BotDecision>) => new Map(prev).set(currentBot.id, decision));
      
      // Wait a bit to show the decision
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Process the bot's action
      try {
        currentState = gameEngine.processPlayerAction(decision.action, decision.amount);
        setGameState(currentState);
        
        // Clear the bot decision after a moment
        setTimeout(() => {
          setBotDecisions((prev: Map<string, BotDecision>) => {
            const newMap = new Map(prev);
            newMap.delete(currentBot.id);
            return newMap;
          });
        }, 2000);
        
        // Wait before next bot if needed
        if (currentState.players[currentState.activePlayerIndex].isBot) {
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
      } catch (error) {
        console.error('Error processing bot action:', error);
        break;
      }
    }
    
    setIsProcessing(false);
  };

  const humanPlayer = gameState.players.find((p: Player) => !p.isBot);
  const isHumanTurn = !isProcessing && 
                     !gameEngine.isGameComplete() && 
                     gameState.players[gameState.activePlayerIndex] === humanPlayer;

  const availableActions = isHumanTurn ? gameEngine.getAvailableActions() : [];
  const winProbability = humanPlayer ? gameEngine.getWinProbability(humanPlayer.id) : 0;

  if (!gameStarted) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-center space-y-6">
          <div className="space-y-4">
            <h1 className="text-6xl font-bold text-white">♠️ PokerBot ♠️</h1>
            <p className="text-xl text-gray-300">Advanced AI Poker Bot - Stages 1-4</p>
          </div>
          
          <div className="bg-slate-800 rounded-lg p-8 max-w-md mx-auto">
            <h2 className="text-2xl font-bold text-white mb-4">Features</h2>
            <ul className="text-left text-gray-300 space-y-2">
              <li>✅ Complete card system & hand evaluation</li>
              <li>✅ Advanced AI decision making</li>
              <li>✅ Probability calculations</li>
              <li>✅ Strategic betting & bluffing</li>
              <li>✅ Multi-phase gameplay (Pre-flop to River)</li>
              <li>✅ Real-time bot reasoning display</li>
            </ul>
          </div>
          
          <button
            onClick={startNewGame}
            className="bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700 text-white font-bold py-4 px-8 rounded-lg text-xl transform hover:scale-105 transition-all duration-200 shadow-lg"
          >
            Start Poker Game
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-green-900 to-slate-900 p-4">
      <div className="max-w-7xl mx-auto">
        <header className="text-center mb-6">
          <h1 className="text-4xl font-bold text-white mb-2">♠️ PokerBot Arena ♠️</h1>
          <p className="text-gray-300">Advanced AI vs Human Poker</p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Left sidebar - Game info */}
          <div className="lg:col-span-1">
            <GameInfo gameState={gameState} winProbability={winProbability} />
            
            {/* Bot thinking displays */}
            {gameState.players
              .filter((p: Player) => p.isBot)
              .map((bot: Player) => (
                <BotThinking
                  key={bot.id}
                  botName={bot.name}
                  decision={botDecisions.get(bot.id)}
                  isThinking={isProcessing && gameState.players[gameState.activePlayerIndex] === bot}
                />
              ))
            }
          </div>

          {/* Main game area */}
          <div className="lg:col-span-3 space-y-6">
            {/* Community cards */}
            <div className="bg-green-800 rounded-xl p-6 shadow-2xl">
              <CommunityCards cards={gameState.communityCards} phase={gameState.phase} />
            </div>

            {/* Players */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {gameState.players.map((player: Player, index: number) => (
                <PlayerHand
                  key={player.id}
                  player={player}
                  communityCards={gameState.communityCards}
                  isActive={gameState.activePlayerIndex === index}
                  showCards={!player.isBot || gameEngine.isGameComplete()}
                />
              ))}
            </div>

            {/* Action buttons for human player */}
            {isHumanTurn && humanPlayer && (
              <div className="bg-slate-800 rounded-lg p-6">
                <h3 className="text-white text-xl font-bold mb-4 text-center">Your Turn</h3>
                <ActionButtons
                  availableActions={availableActions}
                  currentBet={gameState.currentBet}
                  playerBet={humanPlayer.currentBet}
                  playerChips={humanPlayer.chips}
                  onAction={handlePlayerAction}
                  disabled={isProcessing}
                />
              </div>
            )}

            {/* Game complete */}
            {gameEngine.isGameComplete() && (
              <div className="bg-slate-800 rounded-lg p-6 text-center">
                <h3 className="text-white text-2xl font-bold mb-4">Hand Complete!</h3>
                <button
                  onClick={startNewGame}
                  className="bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-lg transform hover:scale-105 transition-all duration-200"
                >
                  Deal New Hand
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;