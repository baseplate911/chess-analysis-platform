import React, { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Chessboard } from 'react-chessboard';
import EvaluationBar from '../components/EvaluationBar';
import MoveList from '../components/MoveList';
import WinProbabilityChart from '../components/WinProbabilityChart';
import GameSummaryCard from '../components/GameSummaryCard';

const STARTING_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';

const classificationEmoji = {
  blunder: '🔴',
  mistake: '🟠',
  inaccuracy: '🟡',
  good: '🟢',
  best: '⭐',
};

export default function LiveGamePage() {
  const navigate = useNavigate();

  const [username, setUsername] = useState('');
  const [status, setStatus] = useState('idle');
  const [gameInfo, setGameInfo] = useState(null);
  const [currentFen, setCurrentFen] = useState(STARTING_FEN);
  const [moves, setMoves] = useState([]);
  const [winProbabilities, setWinProbabilities] = useState([]);
  const [currentEval, setCurrentEval] = useState(0);
  const [lastMove, setLastMove] = useState(null);
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState('');

  const wsRef = useRef(null);
  const connectTimeoutRef = useRef(null);

  const handleConnect = useCallback(() => {
    if (!username.trim()) return;

    setStatus('connecting');
    setError('');
    setMoves([]);
    setWinProbabilities([]);
    setCurrentFen(STARTING_FEN);
    setCurrentEval(0);
    setLastMove(null);
    setSummary(null);
    setGameInfo(null);

    // FIX: Use backend port 8000, not frontend port 5173
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const backendHost = window.location.hostname === 'localhost' 
      ? 'localhost:8000' 
      : window.location.host;
    const wsUrl = `${wsProtocol}//${backendHost}/api/live/ws/${username.trim()}`;

    console.log('🔗 Connecting to:', wsUrl);
    console.log('🔗 Backend Host:', backendHost);
    console.log('🔗 Username:', username.trim());

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    connectTimeoutRef.current = setTimeout(() => {
      if (status === 'connecting') {
        console.log('⏱️ Connection timeout!');
        ws.close();
        setStatus('error');
        setError('Connection timeout. Is backend running on port 8000?');
      }
    }, 10000);

    ws.onopen = () => {
      console.log('✅ WebSocket opened successfully');
      if (connectTimeoutRef.current) {
        clearTimeout(connectTimeoutRef.current);
      }
    };

    ws.onmessage = (event) => {
      console.log('📨 FULL MESSAGE RECEIVED:', event.data);

      let data;
      try {
        data = JSON.parse(event.data);
      } catch (e) {
        console.error('❌ JSON parse error:', e);
        console.error('❌ Raw event data:', event.data);
        return;
      }

      console.log('📨 Parsed data type:', data.type);
      console.log('📨 Full parsed data:', data);

      if (data.type === 'connected') {
        console.log('🎮 Connected to game:', data.game_id);
        setStatus('connected');
        setGameInfo({
          white: data.white,
          black: data.black,
          timeControl: data.time_control,
          gameId: data.game_id,
        });
      }

      if (data.type === 'move') {
        console.log('♟️ Move:', data.move);
        setCurrentFen(data.fen);
        setCurrentEval(data.eval ?? 0);
        setLastMove({
          move: data.move,
          classification: data.classification,
          eval: data.eval,
        });
        setMoves((prev) => [
          ...prev,
          {
            move_number: data.move_number,
            move: data.move,
            classification: data.classification,
            eval_after: data.eval,
          },
        ]);
        setWinProbabilities((prev) => [
          ...prev,
          {
            move: data.move_number,
            white: data.white_win,
            draw: data.draw,
            black: data.black_win,
          },
        ]);
      }

      if (data.type === 'game_over') {
        console.log('🏁 Game over');
        setStatus('game_over');
        setSummary(data.summary);
        if (data.moves && data.moves.length) {
          setMoves(
            data.moves.map((m) => ({
              move_number: m.move_number,
              move: m.move,
              classification: m.classification,
              eval_after: m.eval,
            }))
          );
        }
      }

      if (data.type === 'error') {
        console.error('🔴 Error from backend:', data.message);
        setStatus('error');
        setError(data.message || 'An error occurred.');
        ws.close();
      }
    };

    ws.onerror = (event) => {
      console.error('🔴 WebSocket error event:', event);
      console.error('🔴 WebSocket readyState:', ws.readyState);
      if (connectTimeoutRef.current) {
        clearTimeout(connectTimeoutRef.current);
      }
      setStatus('error');
      setError('WebSocket error. Backend may not be running on port 8000.');
    };

    ws.onclose = (event) => {
      console.log('🔌 WebSocket closed');
      console.log('🔌 Close code:', event.code);
      console.log('🔌 Close reason:', event.reason);
      console.log('🔌 Clean close:', event.wasClean);
      if (connectTimeoutRef.current) {
        clearTimeout(connectTimeoutRef.current);
      }
      if (wsRef.current === ws) {
        wsRef.current = null;
      }
    };
  }, [username, status]);

  const handleStop = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (connectTimeoutRef.current) {
      clearTimeout(connectTimeoutRef.current);
    }
    setStatus('idle');
    setMoves([]);
    setWinProbabilities([]);
    setCurrentFen(STARTING_FEN);
    setCurrentEval(0);
    setLastMove(null);
    setSummary(null);
    setGameInfo(null);
    setError('');
  }, []);

  const moveCount = moves.length;

  return (
    <div className="min-h-screen bg-gray-900 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-2">
              <span className="w-3 h-3 bg-red-500 rounded-full animate-pulse inline-block"></span>
              Live Game Prediction
            </h1>
            <p className="text-gray-400 mt-1">
              Watch your ongoing Lichess game with real-time AI win prediction.
            </p>
          </div>
          <button
            onClick={() => navigate('/analyze')}
            className="text-indigo-400 hover:text-indigo-300 text-sm border border-indigo-500/40 px-3 py-1 rounded-lg transition-colors"
          >
            📋 Analyze Game
          </button>
        </div>

        {status === 'idle' && (
          <div className="max-w-lg mx-auto bg-gray-800 rounded-xl border border-gray-700 p-8 text-center">
            <div className="text-4xl mb-4">🔴</div>
            <h2 className="text-xl font-bold text-white mb-2">Live Game Prediction</h2>
            <p className="text-gray-400 text-sm mb-6">
              Enter your Lichess username to watch your ongoing game with live AI win prediction.
            </p>

            {error && (
              <div className="mb-4 text-red-400 text-sm bg-red-900/20 border border-red-700/40 rounded-lg px-3 py-2 text-left">
                {error}
              </div>
            )}

            <label className="block text-left text-sm font-medium text-gray-300 mb-2">
              Lichess Username
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleConnect()}
                placeholder="e.g. MagnusCarlsen"
                className="flex-1 bg-gray-700 border border-gray-600 text-white rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
              />
              <button
                onClick={handleConnect}
                disabled={!username.trim()}
                className="bg-red-600 hover:bg-red-700 disabled:bg-red-900 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg text-sm font-semibold transition-colors whitespace-nowrap"
              >
                🔴 Watch Live
              </button>
            </div>

            <p className="mt-4 text-xs text-gray-500">
              Make sure you have an ongoing game on Lichess before clicking Watch Live.
            </p>
          </div>
        )}

        {status === 'connecting' && (
          <div className="flex flex-col items-center justify-center py-20 gap-4">
            <div className="w-10 h-10 border-4 border-red-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-gray-400">Connecting to Lichess...</p>
            <p className="text-gray-500 text-xs">Connecting to backend at localhost:8000</p>
            <p className="text-gray-500 text-xs">Check F12 console for detailed logs</p>
          </div>
        )}

        {status === 'error' && (
          <div className="max-w-lg mx-auto bg-gray-800 rounded-xl border border-red-700/40 p-8 text-center">
            <div className="text-4xl mb-4">❌</div>
            <p className="text-red-400 mb-4">{error}</p>
            <details className="text-left bg-gray-900 p-3 rounded text-xs text-gray-400 mb-4">
              <summary className="cursor-pointer font-semibold">Troubleshooting steps</summary>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>Backend running: python backend/main.py</li>
                <li>Port 8000 open: curl http://localhost:8000/health</li>
                <li>Check F12 console for connection logs</li>
                <li>Lichess has ongoing game (start one first)</li>
                <li>Username correct and case-sensitive</li>
                <li>Backend logs should show WebSocket connection</li>
              </ul>
            </details>
            <button
              onClick={() => { setStatus('idle'); setError(''); }}
              className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg text-sm transition-colors"
            >
              Try Again
            </button>
          </div>
        )}

        {(status === 'connected' || status === 'game_over') && gameInfo && (
          <>
            <div className="flex items-center justify-between bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 mb-4">
              <div className="flex items-center gap-3">
                {status === 'connected' ? (
                  <span className="flex items-center gap-1.5 text-green-400 text-sm font-semibold">
                    <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse inline-block"></span>
                    LIVE
                  </span>
                ) : (
                  <span className="flex items-center gap-1.5 text-gray-400 text-sm font-semibold">
                    GAME OVER
                  </span>
                )}
                <span className="text-white text-sm">
                  {gameInfo.white} vs {gameInfo.black}
                </span>
                <span className="text-gray-400 text-xs bg-gray-700/50 px-2 py-0.5 rounded">
                  {gameInfo.timeControl}
                </span>
                {moveCount > 0 && (
                  <span className="text-gray-400 text-xs">Move {moveCount}</span>
                )}
              </div>
              <button
                onClick={handleStop}
                className="bg-gray-700 hover:bg-gray-600 text-white px-3 py-1.5 rounded-lg text-xs transition-colors"
              >
                Stop Watching
              </button>
            </div>

            <div className="flex flex-col lg:flex-row gap-6">
              <div className="flex flex-col items-center gap-4">
                <div className="flex items-start gap-3">
                  <div style={{ width: 420 }}>
                    <Chessboard
                      position={currentFen}
                      boardWidth={420}
                      arePiecesDraggable={false}
                      customBoardStyle={{ borderRadius: '8px', boxShadow: '0 4px 24px rgba(0,0,0,0.4)' }}
                    />
                  </div>
                  <EvaluationBar evaluation={currentEval} />
                </div>

                {lastMove && (
                  <div className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-sm flex items-center gap-3">
                    <span className="text-gray-400">Last Move:</span>
                    <span className="text-white font-mono font-bold">{lastMove.move}</span>
                    <span>{classificationEmoji[lastMove.classification] || ''}</span>
                    <span className="text-gray-400 ml-auto">
                      Eval: {lastMove.eval > 0 ? '+' : ''}{typeof lastMove.eval === 'number' ? lastMove.eval.toFixed(1) : lastMove.eval}
                    </span>
                  </div>
                )}
              </div>

              <div className="flex-1 flex flex-col gap-4">
                <div className="bg-gray-800 rounded-xl border border-gray-700 p-4">
                  <h3 className="text-sm font-semibold text-white mb-3">Win Probability (LIVE)</h3>
                  {winProbabilities.length > 0 ? (
                    (() => {
                      const latest = winProbabilities[winProbabilities.length - 1];
                      return (
                        <div className="space-y-2">
                          {[
                            { label: 'White', value: latest.white, color: 'bg-blue-500' },
                            { label: 'Draw', value: latest.draw, color: 'bg-gray-500' },
                            { label: 'Black', value: latest.black, color: 'bg-red-500' },
                          ].map(({ label, value, color }) => (
                            <div key={label} className="flex items-center gap-2">
                              <span className="text-gray-400 text-xs w-10">{label}</span>
                              <div className="flex-1 bg-gray-700 rounded-full h-3 overflow-hidden">
                                <div
                                  className={`h-full ${color} rounded-full transition-all duration-500`}
                                  style={{ width: `${Math.min(100, value)}%` }}
                                />
                              </div>
                              <span className="text-white text-xs w-12 text-right">{value}%</span>
                            </div>
                          ))}
                        </div>
                      );
                    })()
                  ) : (
                    <p className="text-gray-500 text-sm text-center py-2">Waiting for moves...</p>
                  )}
                </div>

                {winProbabilities.length > 1 && (
                  <div className="bg-gray-800 rounded-xl border border-gray-700 p-4">
                    <h3 className="text-sm font-semibold text-white mb-3">Probability History</h3>
                    <WinProbabilityChart winProbabilities={winProbabilities} />
                  </div>
                )}

                <div className="bg-gray-800 rounded-xl border border-gray-700 p-4">
                  <h3 className="text-sm font-semibold text-white mb-3">Moves</h3>
                  <MoveList
                    moves={moves}
                    currentMoveIndex={moves.length - 1}
                    onMoveClick={() => {}}
                  />
                </div>

                {status === 'game_over' && summary && (
                  <GameSummaryCard summary={summary} result={null} />
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}