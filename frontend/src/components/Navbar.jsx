import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <nav className="bg-gray-900 border-b border-gray-700 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="text-2xl font-bold text-white hover:text-indigo-400 transition-colors">
              ♟ ChessIQ
            </Link>
            {user && (
              <div className="hidden md:flex ml-10 space-x-4">
                <Link
                  to="/dashboard"
                  className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  Dashboard
                </Link>
                <Link
                  to="/analyze"
                  className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  Analyze
                </Link>
                <Link
                  to="/live"
                  className="text-red-400 hover:text-red-300 px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-1"
                >
                  <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse inline-block"></span>
                  Live
                </Link>
                <Link
                  to="/history"
                  className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  History
                </Link>
              </div>
            )}
          </div>

          <div className="hidden md:flex items-center space-x-4">
            {user ? (
              <>
                <span className="text-gray-300 text-sm">
                  👤 {user.username || user.email}
                </span>
                <button
                  onClick={handleLogout}
                  className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link
                  to="/login"
                  className="text-gray-300 hover:text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  Login
                </Link>
                <Link
                  to="/register"
                  className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  Register
                </Link>
              </>
            )}
          </div>

          <div className="md:hidden">
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className="text-gray-400 hover:text-white focus:outline-none p-2"
            >
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                {menuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>
      </div>

      {menuOpen && (
        <div className="md:hidden bg-gray-800 border-t border-gray-700 px-4 py-3 space-y-2">
          {user ? (
            <>
              <Link to="/dashboard" className="block text-gray-300 hover:text-white py-2" onClick={() => setMenuOpen(false)}>Dashboard</Link>
              <Link to="/analyze" className="block text-gray-300 hover:text-white py-2" onClick={() => setMenuOpen(false)}>Analyze</Link>
              <Link to="/live" className="block text-red-400 hover:text-red-300 py-2 flex items-center gap-1" onClick={() => setMenuOpen(false)}>
                <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse inline-block"></span>
                Live
              </Link>
              <Link to="/history" className="block text-gray-300 hover:text-white py-2" onClick={() => setMenuOpen(false)}>History</Link>
              <div className="border-t border-gray-700 pt-2 mt-2">
                <span className="block text-gray-400 text-sm mb-2">👤 {user.username || user.email}</span>
                <button onClick={handleLogout} className="w-full text-left text-gray-300 hover:text-white py-2">Logout</button>
              </div>
            </>
          ) : (
            <>
              <Link to="/login" className="block text-gray-300 hover:text-white py-2" onClick={() => setMenuOpen(false)}>Login</Link>
              <Link to="/register" className="block text-indigo-400 hover:text-indigo-300 py-2" onClick={() => setMenuOpen(false)}>Register</Link>
            </>
          )}
        </div>
      )}
    </nav>
  );
}
