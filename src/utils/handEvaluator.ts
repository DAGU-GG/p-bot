import { Card, Rank, Suit } from '../types/poker';

export interface HandEvaluation {
  handType: string;
  handRank: number;
  kickers: Rank[];
  description: string;
  strength: number; // 0.0 to 1.0
}

export function evaluateHand(cards: Card[]): HandEvaluation {
  if (cards.length < 5) {
    return {
      handType: 'High Card',
      handRank: 1,
      kickers: [],
      description: 'Incomplete hand',
      strength: 0.1
    };
  }

  // Sort cards by rank value (high to low)
  const sortedCards = [...cards].sort((a, b) => getRankValue(b.rank) - getRankValue(a.rank));
  
  // Check for each hand type (from highest to lowest)
  const evaluation = 
    checkStraightFlush(sortedCards) ||
    checkFourOfAKind(sortedCards) ||
    checkFullHouse(sortedCards) ||
    checkFlush(sortedCards) ||
    checkStraight(sortedCards) ||
    checkThreeOfAKind(sortedCards) ||
    checkTwoPair(sortedCards) ||
    checkPair(sortedCards) ||
    checkHighCard(sortedCards);

  return evaluation;
}

function getRankValue(rank: Rank): number {
  const values: Record<Rank, number> = {
    [Rank.TWO]: 2,
    [Rank.THREE]: 3,
    [Rank.FOUR]: 4,
    [Rank.FIVE]: 5,
    [Rank.SIX]: 6,
    [Rank.SEVEN]: 7,
    [Rank.EIGHT]: 8,
    [Rank.NINE]: 9,
    [Rank.TEN]: 10,
    [Rank.JACK]: 11,
    [Rank.QUEEN]: 12,
    [Rank.KING]: 13,
    [Rank.ACE]: 14
  };
  return values[rank];
}

function checkStraightFlush(cards: Card[]): HandEvaluation | null {
  const flush = checkFlush(cards);
  const straight = checkStraight(cards);
  
  if (flush && straight) {
    const highCard = cards[0].rank;
    const isRoyal = getRankValue(highCard) === 14; // Ace high
    
    return {
      handType: isRoyal ? 'Royal Flush' : 'Straight Flush',
      handRank: isRoyal ? 10 : 9,
      kickers: [highCard],
      description: isRoyal ? 'Royal Flush' : `Straight Flush, ${highCard.value} high`,
      strength: isRoyal ? 1.0 : 0.95
    };
  }
  
  return null;
}

function checkFourOfAKind(cards: Card[]): HandEvaluation | null {
  const rankCounts = getRankCounts(cards);
  const fourOfAKindRank = Object.keys(rankCounts).find(rank => rankCounts[rank] === 4);
  
  if (fourOfAKindRank) {
    const kicker = Object.keys(rankCounts).find(rank => rank !== fourOfAKindRank && rankCounts[rank] === 1);
    
    return {
      handType: 'Four of a Kind',
      handRank: 8,
      kickers: kicker ? [kicker as Rank] : [],
      description: `Four ${fourOfAKindRank}s`,
      strength: 0.9
    };
  }
  
  return null;
}

function checkFullHouse(cards: Card[]): HandEvaluation | null {
  const rankCounts = getRankCounts(cards);
  const threeOfAKindRank = Object.keys(rankCounts).find(rank => rankCounts[rank] === 3);
  const pairRank = Object.keys(rankCounts).find(rank => rankCounts[rank] === 2);
  
  if (threeOfAKindRank && pairRank) {
    return {
      handType: 'Full House',
      handRank: 7,
      kickers: [threeOfAKindRank as Rank, pairRank as Rank],
      description: `Full House, ${threeOfAKindRank}s over ${pairRank}s`,
      strength: 0.85
    };
  }
  
  return null;
}

function checkFlush(cards: Card[]): HandEvaluation | null {
  const suitCounts = getSuitCounts(cards);
  const flushSuit = Object.keys(suitCounts).find(suit => suitCounts[suit] >= 5);
  
  if (flushSuit) {
    const flushCards = cards.filter(card => card.suit.toString() === flushSuit);
    const highCard = flushCards[0].rank;
    
    return {
      handType: 'Flush',
      handRank: 6,
      kickers: [highCard],
      description: `Flush, ${highCard.value} high`,
      strength: 0.75
    };
  }
  
  return null;
}

function checkStraight(cards: Card[]): HandEvaluation | null {
  const uniqueRanks = [...new Set(cards.map(card => getRankValue(card.rank)))].sort((a, b) => b - a);
  
  // Check for 5 consecutive ranks
  for (let i = 0; i <= uniqueRanks.length - 5; i++) {
    let consecutive = true;
    for (let j = 1; j < 5; j++) {
      if (uniqueRanks[i + j] !== uniqueRanks[i] - j) {
        consecutive = false;
        break;
      }
    }
    
    if (consecutive) {
      const highCard = Object.values(Rank).find(rank => getRankValue(rank) === uniqueRanks[i]);
      
      return {
        handType: 'Straight',
        handRank: 5,
        kickers: highCard ? [highCard] : [],
        description: `Straight, ${highCard?.value || 'Unknown'} high`,
        strength: 0.65
      };
    }
  }
  
  // Check for A-2-3-4-5 straight (wheel)
  if (uniqueRanks.includes(14) && uniqueRanks.includes(2) && uniqueRanks.includes(3) && 
      uniqueRanks.includes(4) && uniqueRanks.includes(5)) {
    return {
      handType: 'Straight',
      handRank: 5,
      kickers: [Rank.FIVE],
      description: 'Straight, Five high (Wheel)',
      strength: 0.6
    };
  }
  
  return null;
}

function checkThreeOfAKind(cards: Card[]): HandEvaluation | null {
  const rankCounts = getRankCounts(cards);
  const threeOfAKindRank = Object.keys(rankCounts).find(rank => rankCounts[rank] === 3);
  
  if (threeOfAKindRank) {
    const kickers = Object.keys(rankCounts)
      .filter(rank => rank !== threeOfAKindRank && rankCounts[rank] === 1)
      .sort((a, b) => getRankValue(b as Rank) - getRankValue(a as Rank))
      .slice(0, 2) as Rank[];
    
    return {
      handType: 'Three of a Kind',
      handRank: 4,
      kickers,
      description: `Three ${threeOfAKindRank}s`,
      strength: 0.55
    };
  }
  
  return null;
}

function checkTwoPair(cards: Card[]): HandEvaluation | null {
  const rankCounts = getRankCounts(cards);
  const pairs = Object.keys(rankCounts).filter(rank => rankCounts[rank] === 2);
  
  if (pairs.length >= 2) {
    const sortedPairs = pairs.sort((a, b) => getRankValue(b as Rank) - getRankValue(a as Rank));
    const kicker = Object.keys(rankCounts).find(rank => rankCounts[rank] === 1);
    
    return {
      handType: 'Two Pair',
      handRank: 3,
      kickers: kicker ? [kicker as Rank] : [],
      description: `Two Pair, ${sortedPairs[0]}s and ${sortedPairs[1]}s`,
      strength: 0.45
    };
  }
  
  return null;
}

function checkPair(cards: Card[]): HandEvaluation | null {
  const rankCounts = getRankCounts(cards);
  const pairRank = Object.keys(rankCounts).find(rank => rankCounts[rank] === 2);
  
  if (pairRank) {
    const kickers = Object.keys(rankCounts)
      .filter(rank => rank !== pairRank && rankCounts[rank] === 1)
      .sort((a, b) => getRankValue(b as Rank) - getRankValue(a as Rank))
      .slice(0, 3) as Rank[];
    
    return {
      handType: 'Pair',
      handRank: 2,
      kickers,
      description: `Pair of ${pairRank}s`,
      strength: 0.3 + (getRankValue(pairRank as Rank) / 100)
    };
  }
  
  return null;
}

function checkHighCard(cards: Card[]): HandEvaluation {
  const sortedRanks = cards
    .map(card => card.rank)
    .sort((a, b) => getRankValue(b) - getRankValue(a))
    .slice(0, 5);
  
  return {
    handType: 'High Card',
    handRank: 1,
    kickers: sortedRanks,
    description: `High Card, ${sortedRanks[0].value}`,
    strength: 0.1 + (getRankValue(sortedRanks[0]) / 200)
  };
}

function getRankCounts(cards: Card[]): Record<string, number> {
  const counts: Record<string, number> = {};
  
  for (const card of cards) {
    const rank = card.rank.toString();
    counts[rank] = (counts[rank] || 0) + 1;
  }
  
  return counts;
}

function getSuitCounts(cards: Card[]): Record<string, number> {
  const counts: Record<string, number> = {};
  
  for (const card of cards) {
    const suit = card.suit.toString();
    counts[suit] = (counts[suit] || 0) + 1;
  }
  
  return counts;
}