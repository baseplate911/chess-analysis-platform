import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getHistory } from '../api/api';

function ResultBadge({ result }) {
  const styles = {
    win: 'bg-green-900/50 text-green-400 border-green-700/40',
    loss: 'bg-red-900/50 text-red-400 border-red-700/40',
    draw: 'bg-yellow-900/50 text-yellow-400 border-yellow-700/40',
  };
  return (
    <span className={`text-xs font-semibold px-2 py-1 rounded-full border ${styles[result] || 'bg-gray-700 text-gray-400 border-gray-600'}`}>
      {result ? result.charAt(0).toUpperCase() + result.slice(1) : 'Unknown'}
    </span>
  );
}

export default function HistoryPage() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    getHistory()
      .then((res) => setHistory(res.data || []))
      .catch(() => setError('Failed to load game history.'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-400">Loading history...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 py-8 px-4">
      <div className="max-w-5xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-white">Game History</h1>
            <p className="text-gray-400 mt-1">{history.length} game{history.length !== 1 ? 's' : ''} analyzed</p>
          </div>
          <Link
            to="/analyze"
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2.5 rounded-lg text-sm font-semibold transition-colors"
          >
            + Analyze New Game
          </Link>
        </div>

        {error && (
          <div className="mb-6 text-red-400 text-sm bg-red-900/20 border border-red-700/40 rounded-lg px-4 py-3">
            {error}
          </div>
        )}

        {history.length === 0 ? (
          <div className="bg-gray-800 rounded-xl border border-gray-700 py-20 text-center">
            <div className="text-6xl mb-4">♟</div>
            <h2 className="text-xl font-semibold text-white mb-2">No games yet</h2>
            <p className="text-gray-400 mb-6">Analyze your first game to see it here.</p>
            <Link
              to="/analyze"
              className="inline-block bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
            >
              Analyze a Game
            </Link>
          </div>
        ) : (
          <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="text-gray-400 text-xs uppercase border-b border-gray-700 bg-gray-800/80">
                  <th className="px-6 py-4 text-left">#</th>
                  <th className="px-6 py-4 text-left">Date</th>
                  <th className="px-6 py-4 text-left">Result</th>
                  <th className="px-6 py-4 text-left">Moves</th>
                  <th className="px-6 py-4 text-left">Accuracy</th>
                  <th className="px-6 py-4 text-left">Blunders</th>
                  <th className="px-6 py-4 text-left">Actions</th>
                </tr>
              </thead>
              <tbody>
                {history.map((game, i) => (
                  <tr
                    key={game.id || i}
                    className="border-b border-gray-700/50 hover:bg-gray-700/30 transition-colors"
                  >
                    <td className="px-6 py-4 text-gray-500 text-sm">{i + 1}</td>
                    <td className="px-6 py-4 text-gray-300 text-sm">
                      {game.created_at
                        ? new Date(game.created_at).toLocaleDateString(undefined, {
                            year: 'numeric', month: 'short', day: 'numeric',
                          })
                        : '—'}
                    </td>
                    <td className="px-6 py-4">
                      <ResultBadge result={game.result} />
                    </td>
                    <td className="px-6 py-4 text-gray-300 text-sm">{game.move_count || '—'}</td>
                    <td className="px-6 py-4 text-sm">
                      {game.accuracy != null ? (
                        <span className={`font-semibold ${game.accuracy >= 90 ? 'text-green-400' : game.accuracy >= 70 ? 'text-yellow-400' : 'text-red-400'}`}>
                          {game.accuracy.toFixed(1)}%
                        </span>
                      ) : '—'}
                    </td>
                    <td className="px-6 py-4 text-sm">
                      {game.blunders != null ? (
                        <span className={`font-semibold ${game.blunders === 0 ? 'text-green-400' : game.blunders <= 2 ? 'text-yellow-400' : 'text-red-400'}`}>
                          {game.blunders}
                        </span>
                      ) : '—'}
                    </td>
                    <td className="px-6 py-4">
                      {game.pgn ? (
                        <Link
                          to="/analyze"
                          state={{ pgn: game.pgn }}
                          className="text-indigo-400 hover:text-indigo-300 text-xs font-medium transition-colors"
                        >
                          View Analysis →
                        </Link>
                      ) : (
                        <span className="text-gray-600 text-xs">No PGN</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
