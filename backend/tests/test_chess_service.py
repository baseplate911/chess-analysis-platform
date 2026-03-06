"""Tests for the chess analysis service and move classification logic."""

import pytest

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
from services.chess_service import ChessService


# ------------------------------------------------------------------
# classify_move_by_eval_diff
# ------------------------------------------------------------------

class TestClassifyMoveByEvalDiff:
    """Tests for the standalone classification function."""

    def test_blunder(self):
        assert classify_move_by_eval_diff(2.5) == CLASSIFICATION_BLUNDER
        assert classify_move_by_eval_diff(10.0) == CLASSIFICATION_BLUNDER

    def test_mistake(self):
        assert classify_move_by_eval_diff(1.5) == CLASSIFICATION_MISTAKE
        assert classify_move_by_eval_diff(1.01) == CLASSIFICATION_MISTAKE

    def test_inaccuracy(self):
        assert classify_move_by_eval_diff(0.7) == CLASSIFICATION_INACCURACY
        assert classify_move_by_eval_diff(0.51) == CLASSIFICATION_INACCURACY

    def test_good(self):
        assert classify_move_by_eval_diff(0.3) == CLASSIFICATION_GOOD
        assert classify_move_by_eval_diff(0.0) == CLASSIFICATION_GOOD
        assert classify_move_by_eval_diff(-0.4) == CLASSIFICATION_GOOD

    def test_best(self):
        assert classify_move_by_eval_diff(-0.6) == CLASSIFICATION_BEST
        assert classify_move_by_eval_diff(-5.0) == CLASSIFICATION_BEST

    def test_boundary_blunder(self):
        """Exactly at the threshold should NOT be blunder (strict >)."""
        assert classify_move_by_eval_diff(BLUNDER_THRESHOLD) == CLASSIFICATION_MISTAKE

    def test_boundary_mistake(self):
        assert classify_move_by_eval_diff(MISTAKE_THRESHOLD) == CLASSIFICATION_INACCURACY

    def test_boundary_inaccuracy(self):
        assert classify_move_by_eval_diff(INACCURACY_THRESHOLD) == CLASSIFICATION_GOOD

    def test_boundary_good(self):
        assert classify_move_by_eval_diff(GOOD_THRESHOLD) == CLASSIFICATION_BEST


# ------------------------------------------------------------------
# ChessService.classify_move (convenience wrapper)
# ------------------------------------------------------------------

class TestChessServiceClassifyMove:
    """Tests for the ChessService.classify_move static method."""

    def test_delegates_to_shared_function(self):
        assert ChessService.classify_move(5.0, 2.0) == CLASSIFICATION_BLUNDER
        assert ChessService.classify_move(1.0, 1.0) == CLASSIFICATION_GOOD
        assert ChessService.classify_move(0.0, 1.0) == CLASSIFICATION_BEST


# ------------------------------------------------------------------
# ChessService.analyze_game
# ------------------------------------------------------------------

SAMPLE_PGN = """[Event "Test"]
[Site "Test"]
[White "Alice"]
[Black "Bob"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 1-0"""


class TestAnalyzeGame:
    """Integration tests for ChessService.analyze_game."""

    @pytest.fixture(scope="class")
    def analysis(self):
        svc = ChessService()
        return svc.analyze_game(SAMPLE_PGN)

    def test_returns_expected_keys(self, analysis):
        assert set(analysis.keys()) == {"pgn", "result", "moves", "win_probabilities", "summary"}

    def test_move_count(self, analysis):
        assert len(analysis["moves"]) == 6  # 3 moves each

    def test_move_fields(self, analysis):
        move = analysis["moves"][0]
        expected_keys = {
            "move_number", "move", "classification",
            "eval_before", "eval_after", "eval_diff",
            "best_move", "is_capture", "is_check", "is_castle",
        }
        assert set(move.keys()) == expected_keys

    def test_move_annotations_types(self, analysis):
        for m in analysis["moves"]:
            assert isinstance(m["is_capture"], bool)
            assert isinstance(m["is_check"], bool)
            assert isinstance(m["is_castle"], bool)

    def test_best_move_present(self, analysis):
        for m in analysis["moves"]:
            assert isinstance(m["best_move"], str)

    def test_win_probabilities_count(self, analysis):
        assert len(analysis["win_probabilities"]) == len(analysis["moves"])

    def test_win_probabilities_sum_to_100(self, analysis):
        for wp in analysis["win_probabilities"]:
            total = wp["white"] + wp["draw"] + wp["black"]
            assert abs(total - 100.0) < 0.5, f"Win probabilities sum to {total}, expected ~100"

    def test_result(self, analysis):
        assert analysis["result"] == "1-0"

    def test_summary_keys(self, analysis):
        expected_keys = {
            "total_moves", "result",
            "white_blunders", "white_mistakes", "white_inaccuracies", "white_accuracy",
            "black_blunders", "black_mistakes", "black_inaccuracies", "black_accuracy",
        }
        assert set(analysis["summary"].keys()) == expected_keys

    def test_summary_total_moves(self, analysis):
        assert analysis["summary"]["total_moves"] == 6

    def test_summary_accuracy_range(self, analysis):
        assert 0.0 <= analysis["summary"]["white_accuracy"] <= 100.0
        assert 0.0 <= analysis["summary"]["black_accuracy"] <= 100.0

    def test_invalid_pgn(self):
        svc = ChessService()
        with pytest.raises(ValueError, match="Invalid or empty PGN"):
            svc.analyze_game("")


# ------------------------------------------------------------------
# ChessService.analyze_position
# ------------------------------------------------------------------

class TestAnalyzePosition:
    """Tests for single-position analysis."""

    def test_starting_position(self):
        svc = ChessService()
        result = svc.analyze_position("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        assert "evaluation" in result
        assert "best_move" in result
        assert "win_probabilities" in result
        assert isinstance(result["best_move"], str)
        assert len(result["best_move"]) >= 4  # UCI notation, e.g., "e2e4"


# ------------------------------------------------------------------
# ChessService._build_game_summary
# ------------------------------------------------------------------

class TestBuildGameSummary:
    """Tests for the game summary builder."""

    def test_empty_game(self):
        summary = ChessService._build_game_summary([], "*")
        assert summary["total_moves"] == 0
        assert summary["white_accuracy"] == 0.0
        assert summary["black_accuracy"] == 0.0

    def test_all_good_moves(self):
        moves = [
            {"classification": "good"} for _ in range(6)
        ]
        summary = ChessService._build_game_summary(moves, "1-0")
        assert summary["white_accuracy"] == 100.0
        assert summary["black_accuracy"] == 100.0
        assert summary["white_blunders"] == 0

    def test_mixed_classifications(self):
        moves = [
            {"classification": "blunder"},   # white move 1
            {"classification": "good"},      # black move 1
            {"classification": "mistake"},   # white move 2
            {"classification": "best"},      # black move 2
        ]
        summary = ChessService._build_game_summary(moves, "0-1")
        assert summary["white_blunders"] == 1
        assert summary["white_mistakes"] == 1
        assert summary["white_accuracy"] == 0.0  # 0 good/best out of 2
        assert summary["black_accuracy"] == 100.0  # 2 good/best out of 2


# ------------------------------------------------------------------
# ChessService.extract_features
# ------------------------------------------------------------------

class TestExtractFeatures:
    """Tests for the board feature extractor."""

    def test_feature_vector_length(self):
        import chess
        svc = ChessService()
        board = chess.Board()
        features = svc.extract_features(board)
        assert len(features) == 16  # material + 10 piece counts + mobility + 2 doubled pawns + 2 king safety

    def test_starting_position_material_balance(self):
        import chess
        svc = ChessService()
        board = chess.Board()
        features = svc.extract_features(board)
        assert features[0] == 0.0  # Starting position has equal material
