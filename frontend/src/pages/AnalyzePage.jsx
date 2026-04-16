import React, { useState, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Chessboard } from 'react-chessboard';
import { Chess } from 'chess.js';
import { analyzeGame, saveGame } from '../api/api';
import EvaluationBar from '../components/EvaluationBar';
import MoveList from '../components/MoveList';
import WinProbabilityChart from '../components/WinProbabilityChart';
import GameSummaryCard from '../components/GameSummaryCard';

const STARTING_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';

function buildFenArray(pgn) {
  const chess = new Chess();
  try {
    chess.loadPgn(pgn);
  } catch {
    return null;
  }
  const history = chess.history({ verbose: true });
  const fens = [STARTING_FEN];
  const replay = new Chess();
  for (const move of history) {
    replay.move(move.san);
    fens.push(replay.fen());
  }
  return fens;
}

export default function AnalyzePage() {
  const navigate = useNavigate();
  const [pgn, setPgn] = useState('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [analysisData, setAnalysisData] = useState(null);
  const [positions, setPositions] = useState([]);
  const [currentMoveIndex, setCurrentMoveIndex] = useState(-1);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const fileInputRef = useRef(null);

  const currentFen = currentMoveIndex === -1
    ? STARTING_FEN
    : positions[currentMoveIndex + 1] || STARTING_FEN;

  const currentEval = analysisData?.moves?.[currentMoveIndex]?.eval_after ?? 0;
  const currentBestMove = analysisData?.moves?.[currentMoveIndex]?.best_move;

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => setPgn(ev.target.result);
    reader.readAsText(file);
  };

  const handleAnalyze = async () => {
    if (!pgn.trim()) {
      setError('Please enter a PGN to analyze.');
      return;
    }
    setError('');
    setLoading(true);
    setSavedSuccess(false);
    try {
      const res = await analyzeGame(pgn);
      const data = res.data;
      setAnalysisData(data);

      const fens = buildFenArray(pgn);
      if (fens) {
        setPositions(fens);
      } else {
        setError('Could not parse PGN moves for board display.');
        setPositions([STARTING_FEN]);
      }
      setCurrentMoveIndex(-1);
    } catch (err) {
      setError(err.response?.data?.detail || err.response?.data?.message || 'Analysis failed. Please check your PGN.');
    } finally {
      setLoading(false);
    }
  };

  const handlePrev = useCallback(() => {
    setCurrentMoveIndex((i) => Math.max(-1, i - 1));
  }, []);

  const handleNext = useCallback(() => {
    if (!analysisData?.moves) return;
    setCurrentMoveIndex((i) => Math.min(analysisData.moves.length - 1, i + 1));
  }, [analysisData]);

  const handleMoveClick = useCallback((index) => {
    setCurrentMoveIndex(index);
  }, []);

  const handleSave = async () => {
    if (!analysisData) return;
    setSaving(true);
    try {
      await saveGame({ pgn, analysis: analysisData });
      setSavedSuccess(true);
    } catch {
      setError('Failed to save game.');
    } finally {
      setSaving(false);
    }
  };

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'ArrowLeft') handlePrev();
    if (e.key === 'ArrowRight') handleNext();
  }, [handlePrev, handleNext]);

  return (
    <div className="min-h-screen bg-gray-900 py-8 px-4" onKeyDown={handleKeyDown} tabIndex={-1}>
      <div className="max-w-7xl mx-auto">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white">Game Analysis</h1>
            <p className="text-gray-400 mt-1">Paste your PGN below and get AI-powered move-by-move analysis.</p>
          </div>
          <button
            onClick={() => navigate('/live')}
            className="text-red-400 hover:text-red-300 text-sm border border-red-500/40 px-3 py-1 rounded-lg transition-colors flex items-center gap-1"
          >
            <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse inline-block"></span>
            🔴 Live Game →
          </button>
        </div>

        {/* PGN Input */}
        {!analysisData && (
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 mb-6">
            <div className="flex items-center justify-between mb-3">
              <label className="text-sm font-medium text-gray-300">Paste PGN</label>
              <button
                onClick={() => fileInputRef.current?.click()}
                className="text-xs text-indigo-400 hover:text-indigo-300 border border-indigo-500/40 px-3 py-1 rounded-lg transition-colors"
              >
                📂 Upload .pgn file
              </button>
              <input ref={fileInputRef} type="file" accept=".pgn" className="hidden" onChange={handleFileUpload} />
            </div>
            <textarea
              value={pgn}
              onChange={(e) => setPgn(e.target.value)}
              placeholder={`[Event "Example Game"]\n[White "Player1"]\n[Black "Player2"]\n[Result "1-0"]\n\n1. e4 e5 2. Nf3 Nc6 3. Bb5 ...`}
              rows={8}
              className="w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-4 py-3 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent placeholder-gray-500 resize-vertical"
            />
            {error && (
              <div className="mt-3 text-red-400 text-sm bg-red-900/20 border border-red-700/40 rounded-lg px-3 py-2">
                {error}
              </div>
            )}
            <button
              onClick={handleAnalyze}
              disabled={loading}
              className="mt-4 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-800 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg font-semibold text-sm transition-colors flex items-center gap-2"
            >
              {loading && <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />}
              {loading ? 'Analyzing...' : '🔍 Analyze Game'}
            </button>
          </div>
        )}

        {/* Analysis View */}
        {analysisData && (
          <>
            {error && (
              <div className="mb-4 text-red-400 text-sm bg-red-900/20 border border-red-700/40 rounded-lg px-3 py-2">
                {error}
              </div>
            )}

            <div className="flex flex-col lg:flex-row gap-6">
              {/* Left: Board + Controls */}
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
                  <EvaluationBar evaluation={typeof currentEval === 'number' ? currentEval : 0} />
                </div>

                {/* Navigation */}
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setCurrentMoveIndex(-1)}
                    className="bg-gray-700 hover:bg-gray-600 text-white px-3 py-2 rounded-lg text-sm transition-colors"
                    title="Go to start"
                  >
                    ⏮
                  </button>
                  <button
                    onClick={handlePrev}
                    disabled={currentMoveIndex === -1}
                    className="bg-gray-700 hover:bg-gray-600 disabled:opacity-40 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg text-sm transition-colors"
                  >
                    ← Prev
                  </button>
                  <span className="text-gray-400 text-sm w-24 text-center">
                    {currentMoveIndex === -1 ? 'Start' : `Move ${currentMoveIndex + 1} / ${analysisData.moves.length}`}
                  </span>
                  <button
                    onClick={handleNext}
                    disabled={currentMoveIndex === analysisData.moves.length - 1}
                    className="bg-gray-700 hover:bg-gray-600 disabled:opacity-40 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg text-sm transition-colors"
                  >
                    Next →
                  </button>
                  <button
                    onClick={() => setCurrentMoveIndex(analysisData.moves.length - 1)}
                    className="bg-gray-700 hover:bg-gray-600 text-white px-3 py-2 rounded-lg text-sm transition-colors"
                    title="Go to end"
                  >
                    ⏭
                  </button>
                </div>

                {/* Best move */}
                {currentBestMove && (
                  <div className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-sm">
                    <span className="text-gray-400">Best move: </span>
                    <span className="text-indigo-400 font-mono font-bold">{currentBestMove}</span>
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-3 w-full">
                  <button
                    onClick={() => { setAnalysisData(null); setPositions([]); setCurrentMoveIndex(-1); setSavedSuccess(false); setError(''); }}
                    className="flex-1 bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg text-sm transition-colors"
                  >
                    ← New Analysis
                  </button>
                  <button
                    onClick={handleSave}
                    disabled={saving || savedSuccess}
                    className="flex-1 bg-green-700 hover:bg-green-600 disabled:opacity-60 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg text-sm transition-colors"
                  >
                    {savedSuccess ? '✓ Saved' : saving ? 'Saving...' : '💾 Save Game'}
                  </button>
                </div>
              </div>

              {/* Right: Charts + Move List */}
              <div className="flex-1 flex flex-col gap-4">
                {/* Win Probability */}
                <div className="bg-gray-800 rounded-xl border border-gray-700 p-4">
                  <h3 className="text-sm font-semibold text-white mb-3">Win Probability</h3>
                  <WinProbabilityChart winProbabilities={analysisData.win_probabilities || []} />
                </div>

                {/* Move List */}
                <div className="bg-gray-800 rounded-xl border border-gray-700 p-4">
                  <h3 className="text-sm font-semibold text-white mb-3">Moves</h3>
                  <MoveList
                    moves={analysisData.moves || []}
                    currentMoveIndex={currentMoveIndex}
                    onMoveClick={handleMoveClick}
                  />
                </div>

                {/* Summary */}
                {analysisData.moves && analysisData.moves.length > 0 && (
                  (() => {
                    const movesArr = analysisData.moves;
                    const good = movesArr.filter(m => m.classification === 'good').length;
                    const best = movesArr.filter(m => m.classification === 'best').length;
                    const total = movesArr.length;
                   const computedSummary = {
  blunders: movesArr.filter(m => m.classification === 'Blunder').length,
  mistakes: movesArr.filter(m => m.classification === 'Mistake').length,
  inaccuracies: movesArr.filter(m => m.classification === 'Inaccuracy').length,
  good: movesArr.filter(m => m.classification === 'Good').length,
  best: movesArr.filter(m => m.classification === 'Great' || m.classification === 'Brilliant').length,
  total: movesArr.length,
  accuracy: total ? parseFloat(((good + best) / total * 100).toFixed(1)) : 0,
};
                    return (
                      <GameSummaryCard
                        summary={computedSummary}
                        result={analysisData.result}
                      />
                    );
                  })()
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
