import React, { useRef, useEffect } from 'react';

const classificationStyles = {
  blunder: { bg: 'bg-red-100', text: 'text-red-800', emoji: '🔴' },
  mistake: { bg: 'bg-orange-100', text: 'text-orange-800', emoji: '🟠' },
  inaccuracy: { bg: 'bg-yellow-100', text: 'text-yellow-800', emoji: '🟡' },
  good: { bg: 'bg-green-100', text: 'text-green-800', emoji: '🟢' },
  best: { bg: 'bg-blue-100', text: 'text-blue-800', emoji: '⭐' },
};

function MoveChip({ moveData, index, isSelected, onClick }) {
  if (!moveData) return <div className="flex-1" />;

  const style = classificationStyles[moveData.classification] || { bg: 'bg-gray-100', text: 'text-gray-800', emoji: '' };

  return (
    <button
      onClick={() => onClick(index)}
      className={`flex-1 flex items-center gap-1 px-2 py-1 rounded text-xs font-medium transition-all
        ${isSelected
          ? 'ring-2 ring-indigo-500 ' + style.bg + ' ' + style.text
          : style.bg + ' ' + style.text + ' hover:opacity-80'
        }`}
    >
      <span>{style.emoji}</span>
      <span className="font-mono">{moveData.move}</span>
      {moveData.eval !== undefined && (
        <span className="ml-auto opacity-60 text-xs">
          {moveData.eval > 0 ? '+' : ''}{typeof moveData.eval === 'number' ? moveData.eval.toFixed(1) : moveData.eval}
        </span>
      )}
    </button>
  );
}

export default function MoveList({ moves = [], currentMoveIndex, onMoveClick }) {
  const selectedRef = useRef(null);

  useEffect(() => {
    if (selectedRef.current) {
      selectedRef.current.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }
  }, [currentMoveIndex]);

  if (!moves.length) {
    return (
      <div className="text-gray-400 text-sm text-center py-4">
        No moves to display
      </div>
    );
  }

  const movePairs = [];
  for (let i = 0; i < moves.length; i += 2) {
    movePairs.push({
      number: moves[i].move_number || Math.floor(i / 2) + 1,
      white: { data: moves[i], index: i },
      black: moves[i + 1] ? { data: moves[i + 1], index: i + 1 } : null,
    });
  }

  return (
    <div className="overflow-y-auto max-h-64 pr-1 space-y-1">
      {movePairs.map((pair) => (
        <div
          key={pair.number}
          className="flex items-center gap-1"
          ref={
            currentMoveIndex === pair.white.index ||
            (pair.black && currentMoveIndex === pair.black.index)
              ? selectedRef
              : null
          }
        >
          <span className="text-gray-500 text-xs w-7 text-right shrink-0">{pair.number}.</span>
          <MoveChip
            moveData={pair.white.data}
            index={pair.white.index}
            isSelected={currentMoveIndex === pair.white.index}
            onClick={onMoveClick}
          />
          {pair.black ? (
            <MoveChip
              moveData={pair.black.data}
              index={pair.black.index}
              isSelected={currentMoveIndex === pair.black.index}
              onClick={onMoveClick}
            />
          ) : (
            <div className="flex-1" />
          )}
        </div>
      ))}
    </div>
  );
}
