import React from 'react';
import { Link } from 'react-router-dom';

function FeatureCard({ emoji, title, description }) {
  return (
    <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 hover:border-indigo-500 transition-colors">
      <div className="text-4xl mb-4">{emoji}</div>
      <h3 className="text-xl font-semibold text-white mb-2">{title}</h3>
      <p className="text-gray-400 text-sm leading-relaxed">{description}</p>
    </div>
  );
}

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gray-900">
      {/* Hero */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-indigo-900/30 to-gray-900 pointer-events-none" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-24 text-center relative">
          <div className="text-8xl mb-6">♟</div>
          <h1 className="text-5xl sm:text-6xl font-extrabold text-white mb-6 leading-tight">
            AI-Powered<br />
            <span className="text-indigo-400">Chess Analysis</span>
          </h1>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto mb-10 leading-relaxed">
            Upload your games, get deep analysis powered by AI, understand your mistakes, and improve your chess with actionable insights.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/register"
              className="bg-indigo-600 hover:bg-indigo-700 text-white px-8 py-4 rounded-lg text-lg font-semibold transition-colors shadow-lg shadow-indigo-500/25"
            >
              Get Started — It's Free
            </Link>
            <Link
              to="/login"
              className="bg-gray-800 hover:bg-gray-700 text-white px-8 py-4 rounded-lg text-lg font-semibold transition-colors border border-gray-600"
            >
              Login
            </Link>
          </div>
        </div>
      </div>

      {/* Features */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-24">
        <h2 className="text-3xl font-bold text-white text-center mb-4">Everything You Need to Improve</h2>
        <p className="text-gray-400 text-center mb-12 max-w-xl mx-auto">
          ChessIQ provides comprehensive game analysis so you can understand every move and pattern.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <FeatureCard
            emoji="🔍"
            title="Move Analysis"
            description="Every move in your game is evaluated by our AI engine. See blunders, mistakes, inaccuracies, good moves, and best moves highlighted in real time."
          />
          <FeatureCard
            emoji="📈"
            title="Win Probability"
            description="Track how winning chances shift throughout the game with our interactive win probability chart. See exactly when you gained or lost the advantage."
          />
          <FeatureCard
            emoji="🧠"
            title="Player Insights"
            description="Discover your playing style — Aggressive, Defensive, Tactical, or Positional. Get personalized recommendations to take your game to the next level."
          />
        </div>
      </div>

      {/* Stats */}
      <div className="bg-gray-800 border-t border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            {[
              { value: '10K+', label: 'Games Analyzed' },
              { value: '99%', label: 'Accuracy' },
              { value: '< 2s', label: 'Analysis Time' },
              { value: '5K+', label: 'Players' },
            ].map((stat) => (
              <div key={stat.label}>
                <div className="text-3xl font-bold text-indigo-400">{stat.value}</div>
                <div className="text-gray-400 text-sm mt-1">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* CTA */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 text-center">
        <h2 className="text-4xl font-bold text-white mb-6">Ready to improve your chess?</h2>
        <Link
          to="/register"
          className="inline-block bg-indigo-600 hover:bg-indigo-700 text-white px-10 py-4 rounded-lg text-lg font-semibold transition-colors"
        >
          Start Analyzing for Free
        </Link>
      </div>
    </div>
  );
}
