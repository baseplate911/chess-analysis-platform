import React from 'react';

const classificationConfig = {
  blunder: { emoji: '🔴', label: 'Blunders', color: 'text-red-400', bg: 'bg-red-900/20 border-red-700/40' },
  mistake: { emoji: '🟠', label: 'Mistakes', color: 'text-orange-400', bg: 'bg-orange-900/20 border-orange-700/40' },
  inaccuracy: { emoji: '🟡', label: 'Inaccuracies', color: 'text-yellow-400', bg: 'bg-yellow-900/20 border-yellow-700/40' },
  good: { emoji: '🟢', label: 'Good Moves', color: 'text-green-400', bg: 'bg-green-900/20 border-green-700/40' },
  great: { emoji: '⭐', label: 'Great Moves', color: 'text-blue-400', bg: 'bg-blue-900/20 border-blue-700/40' },
  brilliant: { emoji: '💫', label: 'Brilliant Moves', color: 'text-purple-400', bg: 'bg-purple-900/20 border-purple-700/40' },
  accuracy: { emoji: '📊', label: 'Accuracy', color: 'text-indigo-400', bg: 'bg-indigo-900/20 border-indigo-700/40' },
};

export default function GameSummaryCard({ summary, result }) {
  if (!summary) return null;

  const stats = [
    { key: 'blunder', value: summary.blunders },
    { key: 'mistake', value: summary.mistakes },
    { key: 'inaccuracy', value: summary.inaccuracies },
    { key: 'good', value: summary.good },
    { key: 'great', value: summary.great },
    { key: 'brilliant', value: summary.brilliant },
    { key: 'accuracy', value: `${summary.accuracy}%` },
  ];

  return (
    <div className="bg-gray-800 rounded-xl border border-gray-700 p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-white">Game Summary</h3>
        {result && (
          <span className="text-xs text-gray-400 bg-gray-700/50 px-2 py-1 rounded">
            Result: {result}
          </span>
        )}
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {stats.map(({ key, value }) => {
          const cfg = classificationConfig[key];
          return (
            <div
              key={key}
              className={`rounded-lg border px-3 py-2 ${cfg.bg}`}
            >
              <div className="text-xs text-gray-400 flex items-center gap-1">
                <span>{cfg.emoji}</span>
                <span>{cfg.label}</span>
              </div>
              <div className={`text-lg font-bold mt-0.5 ${cfg.color}`}>{value}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}