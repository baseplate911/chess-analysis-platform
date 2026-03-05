import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getHistory, getProfile, classifyPlayer } from '../api/api';

function StatCard({ icon, label, value, color = 'indigo' }) {
  const colorMap = {
    indigo: 'from-indigo-500/20 to-indigo-600/10 border-indigo-500/30 text-indigo-400',
    green: 'from-green-500/20 to-green-600/10 border-green-500/30 text-green-400',
    blue: 'from-blue-500/20 to-blue-600/10 border-blue-500/30 text-blue-400',
    purple: 'from-purple-500/20 to-purple-600/10 border-purple-500/30 text-purple-400',
  };
  return (
    <div className={`bg-gradient-to-br ${colorMap[color]} border rounded-xl p-5`}>
      <div className="text-3xl mb-2">{icon}</div>
      <div className={`text-2xl font-bold ${colorMap[color].split(' ').pop()}`}>{value}</div>
      <div className="text-gray-400 text-sm mt-1">{label}</div>
    </div>
  );
}

const styleEmoji = {
  Aggressive: '⚔️',
  Defensive: '🛡️',
  Tactical: '🎯',
  Positional: '♟',
};

export default function Dashboard() {
  const { user } = useAuth();
  const [history, setHistory] = useState([]);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.allSettled([getHistory(), getProfile()])
      .then(([histRes, profRes]) => {
        if (histRes.status === 'fulfilled') {
          setHistory(histRes.value.data || []);
        }
        if (profRes.status === 'fulfilled') {
          setProfile(profRes.value.data);
        }
      })
      .finally(() => setLoading(false));
  }, []);

  const totalGames = history.length;
  const avgAccuracy = history.length
    ? (history.reduce((sum, g) => sum + (g.accuracy || 0), 0) / history.length).toFixed(1)
    : '—';
  const wins = history.filter((g) => g.result === 'win').length;
  const winRate = totalGames ? `${Math.round((wins / totalGames) * 100)}%` : '—';

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-400">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">
            Welcome back, <span className="text-indigo-400">{user?.username || 'Player'}</span> 👋
          </h1>
          <p className="text-gray-400 mt-1">Here's your chess performance overview.</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard icon="🎮" label="Total Games" value={totalGames} color="indigo" />
          <StatCard icon="🎯" label="Avg. Accuracy" value={avgAccuracy !== '—' ? `${avgAccuracy}%` : '—'} color="green" />
          <StatCard icon="🏆" label="Win Rate" value={winRate} color="blue" />
          <StatCard icon="♟" label="Player Style" value={profile?.style || '—'} color="purple" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Games */}
          <div className="lg:col-span-2 bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-700 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">Recent Games</h2>
              <Link to="/history" className="text-indigo-400 hover:text-indigo-300 text-sm">
                View all →
              </Link>
            </div>
            {history.length === 0 ? (
              <div className="py-12 text-center">
                <div className="text-4xl mb-3">♟</div>
                <p className="text-gray-400">No games yet.</p>
                <Link
                  to="/analyze"
                  className="mt-4 inline-block bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2 rounded-lg text-sm"
                >
                  Analyze Your First Game
                </Link>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-gray-400 text-xs uppercase border-b border-gray-700">
                      <th className="px-6 py-3 text-left">Date</th>
                      <th className="px-6 py-3 text-left">Result</th>
                      <th className="px-6 py-3 text-left">Moves</th>
                      <th className="px-6 py-3 text-left">Accuracy</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.slice(0, 5).map((game, i) => (
                      <tr key={i} className="border-b border-gray-700/50 hover:bg-gray-700/30 transition-colors">
                        <td className="px-6 py-4 text-gray-300 text-sm">
                          {game.created_at ? new Date(game.created_at).toLocaleDateString() : '—'}
                        </td>
                        <td className="px-6 py-4">
                          <span className={`text-xs font-semibold px-2 py-1 rounded-full ${
                            game.result === 'win' ? 'bg-green-900/50 text-green-400' :
                            game.result === 'loss' ? 'bg-red-900/50 text-red-400' :
                            'bg-gray-700 text-gray-400'
                          }`}>
                            {game.result || 'Unknown'}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-gray-300 text-sm">{game.move_count || '—'}</td>
                        <td className="px-6 py-4 text-gray-300 text-sm">
                          {game.accuracy ? `${game.accuracy.toFixed(1)}%` : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Player Profile */}
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Player Profile</h2>
            {profile ? (
              <div className="space-y-4">
                <div className="text-center py-4">
                  <div className="text-6xl mb-3">{styleEmoji[profile.style] || '♟'}</div>
                  <div className="text-xl font-bold text-indigo-400">{profile.style || 'Unknown'}</div>
                  <div className="text-gray-400 text-sm mt-1">Playing Style</div>
                </div>
                {profile.strengths && (
                  <div>
                    <div className="text-xs uppercase text-gray-500 mb-2 font-semibold">Strengths</div>
                    <div className="flex flex-wrap gap-1">
                      {profile.strengths.map((s, i) => (
                        <span key={i} className="bg-green-900/40 text-green-400 text-xs px-2 py-1 rounded-full">{s}</span>
                      ))}
                    </div>
                  </div>
                )}
                {profile.weaknesses && (
                  <div>
                    <div className="text-xs uppercase text-gray-500 mb-2 font-semibold">Areas to Improve</div>
                    <div className="flex flex-wrap gap-1">
                      {profile.weaknesses.map((w, i) => (
                        <span key={i} className="bg-red-900/40 text-red-400 text-xs px-2 py-1 rounded-full">{w}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-6">
                <div className="text-4xl mb-3">📊</div>
                <p className="text-gray-400 text-sm mb-4">Analyze more games to unlock your player profile.</p>
                <Link
                  to="/analyze"
                  className="inline-block bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg text-sm"
                >
                  Analyze a Game
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
