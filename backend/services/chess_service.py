"""Chess analysis service using python-chess with an optional Stockfish backend.

Move classification thresholds (in pawns, from the moving side's perspective):

    +-----------------+--------------------------------------+
    | Classification  | Condition (eval_diff = before-after) |
    +-----------------+--------------------------------------+
    | blunder         | eval_diff > 2.0                      |
    | mistake         | eval_diff > 1.0                      |
    | inaccuracy      | eval_diff > 0.5                      |
    | good            | eval_diff > -0.5                     |
    | best            | eval_diff <= -0.5                    |
    +-----------------+--------------------------------------+

A positive ``eval_diff`` means the position worsened for the moving
player; a negative value means the position improved (the move was
better than the engine's expectation).
"""

import io
import math
from typing import Dict, List, Optional

import chess
import chess.pgn

from services.ml_service import MLService
from services.move_classification import (
    BLUNDER_THRESHOLD,
    CLASSIFICATION_BEST,
    CLASSIFICATION_BLUNDER,
    CLASSIFICATION_GOOD,
    CLASSIFICATION_INACCURACY,
    CLASSIFICATION_MISTAKE,
    GOOD_THRESHOLD,
    INACCURACY_THRESHOLD,
    MISTAKE_THRESHOLD,
    classify_move_by_eval_diff,
)


class ChessService:
    """Provides chess game and position analysis, using Stockfish when available."""

    def __init__(self):
        self.ml_service = MLService()
        self.engine = None
        self._try_load_stockfish()

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------

    def _try_load_stockfish(self) -> None:
        """Attempt to load the Stockfish engine; silently fall back to heuristics."""
        try:
            import chess.engine
            self.engine = chess.engine.SimpleEngine.popen_uci("stockfish")
        except Exception:
            self.engine = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze_game(self, pgn_string: str) -> Dict:
        """Analyse every move in a PGN game.

        Returns a dict containing:
        - ``pgn``: the original PGN text
        - ``result``: the game result header (e.g. ``"1-0"``)
        - ``moves``: per-move analysis list (classification, eval, best_move, annotations)
        - ``win_probabilities``: per-move win/draw/loss percentages
        - ``summary``: aggregate statistics (accuracy, blunder/mistake/inaccuracy counts, …)
        """
        pgn_io = io.StringIO(pgn_string)
        game = chess.pgn.read_game(pgn_io)
        if game is None:
            raise ValueError("Invalid or empty PGN string")

        board = game.board()
        moves_analysis: List[Dict] = []
        win_probabilities: List[Dict] = []
        move_number = 0

        eval_before = self._evaluate_position(board)

        for node in game.mainline():
            move = node.move
            move_san = board.san(move)
            is_white = board.turn == chess.WHITE

            # Collect move annotations *before* pushing
            is_capture = board.is_capture(move)
            is_castle = board.is_castling(move)

            # Determine best move *before* the current move is played
            best_move = self._get_best_move(board)

            board.push(move)
            move_number += 1

            # Collect annotations that require the *new* position
            is_check = board.is_check()

            eval_after = self._evaluate_position(board)
            perspective_before = eval_before if is_white else -eval_before
            perspective_after = eval_after if is_white else -eval_after
            eval_diff = perspective_before - perspective_after

            classification = classify_move_by_eval_diff(eval_diff)
            features = self.extract_features(board)

            # Use eval_after (white's perspective) to compute win probability
            probs = self.ml_service.predict_win_probability([eval_after] + features[1:])

            moves_analysis.append(
                {
                    "move_number": move_number,
                    "move": move_san,
                    "classification": classification,
                    "eval_before": round(perspective_before, 3),
                    "eval_after": round(perspective_after, 3),
                    "eval_diff": round(eval_diff, 3),
                    "best_move": best_move,
                    "is_capture": is_capture,
                    "is_check": is_check,
                    "is_castle": is_castle,
                }
            )
            win_probabilities.append(
                {
                    "move": move_number,
                    "white": round(probs[0] * 100, 1),
                    "draw": round(probs[1] * 100, 1),
                    "black": round(probs[2] * 100, 1),
                }
            )

            eval_before = eval_after

        result = game.headers.get("Result", "*")
        summary = self._build_game_summary(moves_analysis, result)

        return {
            "pgn": pgn_string,
            "result": result,
            "moves": moves_analysis,
            "win_probabilities": win_probabilities,
            "summary": summary,
        }

    def analyze_position(self, fen: str) -> Dict:
        """Evaluate a single board position given in FEN notation."""
        board = chess.Board(fen)
        evaluation = self._evaluate_position(board)
        features = self.extract_features(board)
        probs = self.ml_service.predict_win_probability([evaluation] + features[1:])

        best_move = self._get_best_move(board)

        return {
            "evaluation": round(evaluation, 3),
            "best_move": best_move,
            "win_probabilities": {
                "white": round(probs[0] * 100, 1),
                "draw": round(probs[1] * 100, 1),
                "black": round(probs[2] * 100, 1),
            },
        }

    @staticmethod
    def classify_move(eval_before: float, eval_after: float) -> str:
        """Classify a move based on the evaluation change from the current player's perspective.

        This is a convenience wrapper around :func:`classify_move_by_eval_diff`.
        """
        return classify_move_by_eval_diff(eval_before - eval_after)

    def extract_features(self, board: chess.Board) -> List[float]:
        """Extract a numeric feature vector from a chess board for ML input."""
        features: List[float] = []

        piece_values = {
            chess.PAWN: 1.0,
            chess.KNIGHT: 3.0,
            chess.BISHOP: 3.0,
            chess.ROOK: 5.0,
            chess.QUEEN: 9.0,
            chess.KING: 0.0,
        }

        white_material = sum(
            piece_values[pt] * len(board.pieces(pt, chess.WHITE))
            for pt in piece_values
        )
        black_material = sum(
            piece_values[pt] * len(board.pieces(pt, chess.BLACK))
            for pt in piece_values
        )
        features.append(white_material - black_material)

        for color in [chess.WHITE, chess.BLACK]:
            for pt in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
                features.append(float(len(board.pieces(pt, color))))

        # Mobility
        features.append(float(board.legal_moves.count()))

        # Pawn structure: doubled pawns per side
        for color in [chess.WHITE, chess.BLACK]:
            pawn_files = [chess.square_file(sq) for sq in board.pieces(chess.PAWN, color)]
            doubled = sum(pawn_files.count(f) - 1 for f in set(pawn_files))
            features.append(float(doubled))

        # King safety
        for color in [chess.WHITE, chess.BLACK]:
            king_sq = board.king(color)
            if king_sq is not None:
                attackers = len(board.attackers(not color, king_sq))
                features.append(float(attackers))
            else:
                features.append(0.0)

        return features

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _evaluate_position(self, board: chess.Board) -> float:
        """Return evaluation of the position (positive = White advantage)."""
        if self.engine:
            try:
                import chess.engine
                info = self.engine.analyse(board, chess.engine.Limit(depth=12))
                score = info["score"].white()
                if score.is_mate():
                    mate_in = score.mate()
                    return 100.0 if mate_in and mate_in > 0 else -100.0
                cp = score.score()
                return (cp or 0) / 100.0
            except Exception:
                pass

        return self._heuristic_evaluation(board)

    def _heuristic_evaluation(self, board: chess.Board) -> float:
        """
        Enhanced evaluation combining:
        - Material balance
        - Center control bonus
        - Piece mobility bonus
        - Pawn advancement bonus
        - Castling bonus
        - Check/threat penalty
        """
        piece_values = {
            chess.PAWN: 1.0,
            chess.KNIGHT: 3.0,
            chess.BISHOP: 3.25,
            chess.ROOK: 5.0,
            chess.QUEEN: 9.0,
            chess.KING: 0.0,
        }

        # 1. Material balance
        score = 0.0
        for piece_type, value in piece_values.items():
            score += value * len(board.pieces(piece_type, chess.WHITE))
            score -= value * len(board.pieces(piece_type, chess.BLACK))

        # 2. Center control bonus (e4,d4,e5,d5 squares)
        center_squares = [chess.E4, chess.D4, chess.E5, chess.D5]
        for sq in center_squares:
            white_attackers = len(board.attackers(chess.WHITE, sq))
            black_attackers = len(board.attackers(chess.BLACK, sq))
            score += 0.1 * (white_attackers - black_attackers)

        # 3. Mobility bonus
        current_turn = board.turn
        board.turn = chess.WHITE
        white_moves = board.legal_moves.count()
        board.turn = chess.BLACK
        black_moves = board.legal_moves.count()
        board.turn = current_turn
        score += 0.05 * (white_moves - black_moves)

        # 4. Pawn advancement bonus
        for sq in board.pieces(chess.PAWN, chess.WHITE):
            score += 0.05 * (chess.square_rank(sq) - 1)
        for sq in board.pieces(chess.PAWN, chess.BLACK):
            score -= 0.05 * (6 - chess.square_rank(sq))

        # 5. Castling rights bonus
        if board.has_castling_rights(chess.WHITE):
            score += 0.2
        if board.has_castling_rights(chess.BLACK):
            score -= 0.2

        # 6. Check penalty/bonus
        if board.is_check():
            if board.turn == chess.BLACK:
                score += 0.5  # White just gave check
            else:
                score -= 0.5

        return score

    def _get_best_move(self, board: chess.Board) -> str:
        """Return the best move in UCI notation, falling back to the first legal move."""
        if self.engine:
            try:
                import chess.engine
                result = self.engine.play(board, chess.engine.Limit(depth=12))
                return result.move.uci() if result.move else ""
            except Exception:
                pass

        # Fallback: return first legal move
        for move in board.legal_moves:
            return move.uci()
        return ""

    @staticmethod
    def _build_game_summary(moves_analysis: List[Dict], result: str) -> Dict:
        """Compute aggregate statistics for the analysed game.

        Returns a dict with keys:
        - ``total_moves``: total number of half-moves
        - ``result``: the game result string (e.g. ``"1-0"``)
        - ``white_blunders``, ``white_mistakes``, ``white_inaccuracies``
        - ``black_blunders``, ``black_mistakes``, ``black_inaccuracies``
        - ``white_accuracy``, ``black_accuracy``: percentage of moves
          classified as "good" or "best" for each side
        """
        total = len(moves_analysis)

        counts: Dict[str, Dict[str, int]] = {
            "white": {CLASSIFICATION_BLUNDER: 0, CLASSIFICATION_MISTAKE: 0, CLASSIFICATION_INACCURACY: 0,
                      CLASSIFICATION_GOOD: 0, CLASSIFICATION_BEST: 0},
            "black": {CLASSIFICATION_BLUNDER: 0, CLASSIFICATION_MISTAKE: 0, CLASSIFICATION_INACCURACY: 0,
                      CLASSIFICATION_GOOD: 0, CLASSIFICATION_BEST: 0},
        }

        for i, m in enumerate(moves_analysis):
            side = "white" if i % 2 == 0 else "black"
            cls = m.get("classification", CLASSIFICATION_GOOD)
            if cls in counts[side]:
                counts[side][cls] += 1

        def _accuracy(side_counts: Dict[str, int]) -> float:
            side_total = sum(side_counts.values())
            if side_total == 0:
                return 0.0
            good_or_best = side_counts[CLASSIFICATION_GOOD] + side_counts[CLASSIFICATION_BEST]
            return round(good_or_best / side_total * 100, 1)

        return {
            "total_moves": total,
            "result": result,
            "white_blunders": counts["white"][CLASSIFICATION_BLUNDER],
            "white_mistakes": counts["white"][CLASSIFICATION_MISTAKE],
            "white_inaccuracies": counts["white"][CLASSIFICATION_INACCURACY],
            "white_accuracy": _accuracy(counts["white"]),
            "black_blunders": counts["black"][CLASSIFICATION_BLUNDER],
            "black_mistakes": counts["black"][CLASSIFICATION_MISTAKE],
            "black_inaccuracies": counts["black"][CLASSIFICATION_INACCURACY],
            "black_accuracy": _accuracy(counts["black"]),
        }

    def __del__(self):
        """Clean up the Stockfish engine process on garbage collection."""
        if self.engine:
            try:
                self.engine.quit()
            except Exception:
                pass
