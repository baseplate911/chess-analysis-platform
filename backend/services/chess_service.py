"""Chess analysis service using python-chess with an optional Stockfish backend.
"""

import io
import math
from typing import Dict, List, Optional

import chess
import chess.pgn

from services.ml_service import MLService


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
        """Analyse every move in a PGN game and return classifications and win probabilities."""
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

            board.push(move)
            move_number += 1

            eval_after = self._evaluate_position(board)
            perspective_before = eval_before if is_white else -eval_before
            perspective_after = eval_after if is_white else -eval_after
            eval_diff = perspective_before - perspective_after

            classification = self.classify_move(perspective_before, perspective_after)
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
        return {
            "pgn": pgn_string,
            "result": result,
            "moves": moves_analysis,
            "win_probabilities": win_probabilities,
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

    def classify_move(self, eval_before: float, eval_after: float) -> str:
        """Classify a move based on the evaluation change from the current player's perspective."""
        eval_diff = eval_before - eval_after
        if eval_diff > 2.0:
            return "blunder"
        if eval_diff > 1.0:
            return "mistake"
        if eval_diff > 0.5:
            return "inaccuracy"
        if eval_diff > -0.5:
            return "good"
        return "best"

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

    def __del__(self):
        """Clean up the Stockfish engine process on garbage collection."""
        if self.engine:
            try:
                self.engine.quit()
            except Exception:
                pass
