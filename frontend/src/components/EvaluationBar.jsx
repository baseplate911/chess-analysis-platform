import React from 'react';

export default function EvaluationBar({ evaluation = 0 }) {
  const clampedEval = Math.max(-10, Math.min(10, evaluation));
  const whitePercent = ((clampedEval + 10) / 20) * 100;
  const blackPercent = 100 - whitePercent;

  const displayEval = evaluation > 0
    ? `+${evaluation.toFixed(1)}`
    : evaluation.toFixed(1);

  return (
    <div className="flex flex-col items-center h-full">
      <div className="relative w-8 bg-gray-700 rounded overflow-hidden" style={{ height: '400px' }}>
        <div
          className="absolute top-0 left-0 w-full bg-gray-900 transition-all duration-300"
          style={{ height: `${blackPercent}%` }}
        />
        <div
          className="absolute bottom-0 left-0 w-full bg-white transition-all duration-300"
          style={{ height: `${whitePercent}%` }}
        />
        <div className="absolute inset-0 flex items-center justify-center">
          <div
            className="w-0.5 h-full opacity-30"
            style={{ background: 'linear-gradient(to bottom, transparent 49%, #6b7280 49%, #6b7280 51%, transparent 51%)' }}
          />
        </div>
      </div>
      <div className={`mt-2 text-xs font-bold ${evaluation >= 0 ? 'text-white' : 'text-gray-400'}`}>
        {displayEval}
      </div>
    </div>
  );
}
