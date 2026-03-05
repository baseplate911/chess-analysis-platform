"""
Feature Extractor
=================
Converts a ``chess.Board`` position into a fixed-length numeric feature vector
suitable for the ML models in this package.

Feature vector (16 floats, in order):
    0  material_balance       – centipawn balance (+ = white ahead)
    1  white_material         – total white material in centipawns
    2  black_material         – total black material in centipawns
    3  white_mobility         – number of legal moves available to white
    4  black_mobility         – number of legal moves available to black
    5  king_safety_white      – simplified white king safety score
    6  king_safety_black      – simplified black king safety score
    7  center_control         – white centre control minus black centre control
    8  pawn_structure         – doubled/isolated pawn penalty (negative = worse)
    9  castling_rights        – encoded castling availability (0–3)
    10 move_number            – full-move number
    11 is_check               – 1 if the side to move is in check, else 0
    12 is_endgame             – 1 if total material ≤ 1300 centipawns, else 0
    13 material_ratio         – white_material / (white_material + black_material)
    14 space_advantage        – white advanced pawns minus black advanced pawns
    15 development_score      – white minor pieces developed minus black
"""

import logging
from typing import List

import chess

logger = logging.getLogger(__name__)

_PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}

_CENTRE_SQUARES = {chess.E4, chess.D4, chess.E5, chess.D5}
_EXTENDED_CENTRE = {chess.C3, chess.D3, chess.E3, chess.F3,
                    chess.C4, chess.F4, chess.C5, chess.F5,
                    chess.C6, chess.D6, chess.E6, chess.F6}

_N_FEATURES = 16


class FeatureExtractor:
    """Extract a fixed-length feature vector from a chess board position."""

    def extract_features(self, board: chess.Board) -> List[float]:
        """Return a list of 16 floats describing *board*.

        Parameters
        ----------
        board:
            A ``chess.Board`` instance at any position.

        Returns
        -------
        List of 16 floats (see module docstring for semantics).
        """
        white_mat = self._material(board, chess.WHITE)
        black_mat = self._material(board, chess.BLACK)
        material_balance = white_mat - black_mat

        white_mobility = self._mobility(board, chess.WHITE)
        black_mobility = self._mobility(board, chess.BLACK)

        king_safety_white = self._king_safety(board, chess.WHITE)
        king_safety_black = self._king_safety(board, chess.BLACK)

        center_control = self._center_control(board)
        pawn_structure = self._pawn_structure(board)

        castling_rights = self._castling_rights(board)
        move_number = float(board.fullmove_number)
        is_check = 1.0 if board.is_check() else 0.0
        is_endgame = 1.0 if (white_mat + black_mat) <= 1300 else 0.0
        total_mat = white_mat + black_mat
        material_ratio = white_mat / total_mat if total_mat > 0 else 0.5

        space_advantage = self._space_advantage(board)
        development_score = self._development_score(board)

        return [
            material_balance,
            white_mat,
            black_mat,
            white_mobility,
            black_mobility,
            king_safety_white,
            king_safety_black,
            center_control,
            pawn_structure,
            castling_rights,
            move_number,
            is_check,
            is_endgame,
            material_ratio,
            space_advantage,
            development_score,
        ]

    def normalize_features(self, features: List[float]) -> List[float]:
        """Return a normalised copy of *features*.

        Each feature is divided by a hand-tuned scale factor so that the
        resulting values are roughly in the range [−1, 1] for typical
        mid-game positions.
        """
        if len(features) != _N_FEATURES:
            raise ValueError(
                f"Expected {_N_FEATURES} features, got {len(features)}"
            )

        scales = [
            3900.0,  # material_balance  (max ~39 pawns)
            3900.0,  # white_material
            3900.0,  # black_material
            50.0,    # white_mobility
            50.0,    # black_mobility
            10.0,    # king_safety_white
            10.0,    # king_safety_black
            10.0,    # center_control
            20.0,    # pawn_structure
            3.0,     # castling_rights
            100.0,   # move_number
            1.0,     # is_check (already 0/1)
            1.0,     # is_endgame (already 0/1)
            1.0,     # material_ratio (already 0–1)
            8.0,     # space_advantage
            8.0,     # development_score
        ]

        return [f / s if s != 0 else f for f, s in zip(features, scales)]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _material(board: chess.Board, color: chess.Color) -> float:
        total = 0.0
        for piece_type, value in _PIECE_VALUES.items():
            total += value * len(board.pieces(piece_type, color))
        return total

    @staticmethod
    def _mobility(board: chess.Board, color: chess.Color) -> float:
        """Count legal moves for *color* without permanently altering the board."""
        if board.turn == color:
            return float(board.legal_moves.count())
        # Temporarily flip the turn to count the other side's moves, then restore
        original_turn = board.turn
        board.turn = color
        count = float(board.legal_moves.count())
        board.turn = original_turn
        return count

    @staticmethod
    def _king_safety(board: chess.Board, color: chess.Color) -> float:
        """Rough king safety: number of friendly pieces adjacent to the king."""
        king_sq = board.king(color)
        if king_sq is None:
            return 0.0
        adjacent = chess.SquareSet(chess.BB_KING_ATTACKS[king_sq])
        shield = sum(1 for sq in adjacent if board.color_at(sq) == color)
        return float(shield)

    @staticmethod
    def _center_control(board: chess.Board) -> float:
        """White centre attacks minus black centre attacks."""
        score = 0.0
        for sq in _CENTRE_SQUARES:
            score += len(board.attackers(chess.WHITE, sq))
            score -= len(board.attackers(chess.BLACK, sq))
        return score

    @staticmethod
    def _pawn_structure(board: chess.Board) -> float:
        """Negative penalty for doubled/isolated pawns (white minus black)."""

        def _penalty(color: chess.Color) -> float:
            pawns = board.pieces(chess.PAWN, color)
            penalty = 0.0
            files = [chess.square_file(sq) for sq in pawns]
            for f in range(8):
                file_count = files.count(f)
                if file_count > 1:
                    penalty += (file_count - 1)  # doubled
                if file_count > 0:
                    has_neighbour = (f > 0 and (f - 1) in files) or (
                        f < 7 and (f + 1) in files
                    )
                    if not has_neighbour:
                        penalty += 1  # isolated
            return penalty

        return _penalty(chess.BLACK) - _penalty(chess.WHITE)

    @staticmethod
    def _castling_rights(board: chess.Board) -> float:
        """Encode castling rights as a 0–3 score for white and 0–3 for black."""
        rights = 0.0
        if board.has_kingside_castling_rights(chess.WHITE):
            rights += 1
        if board.has_queenside_castling_rights(chess.WHITE):
            rights += 1
        if board.has_kingside_castling_rights(chess.BLACK):
            rights += 1
        if board.has_queenside_castling_rights(chess.BLACK):
            rights += 1
        return rights

    @staticmethod
    def _space_advantage(board: chess.Board) -> float:
        """White pawns past rank 4 minus black pawns past rank 5."""
        white_advanced = sum(
            1 for sq in board.pieces(chess.PAWN, chess.WHITE)
            if chess.square_rank(sq) >= 4
        )
        black_advanced = sum(
            1 for sq in board.pieces(chess.PAWN, chess.BLACK)
            if chess.square_rank(sq) <= 3
        )
        return float(white_advanced - black_advanced)

    @staticmethod
    def _development_score(board: chess.Board) -> float:
        """Minor pieces off back rank (white) minus those still on back rank (black)."""
        white_developed = sum(
            1 for sq in (
                list(board.pieces(chess.KNIGHT, chess.WHITE))
                + list(board.pieces(chess.BISHOP, chess.WHITE))
            )
            if chess.square_rank(sq) != 0
        )
        black_developed = sum(
            1 for sq in (
                list(board.pieces(chess.KNIGHT, chess.BLACK))
                + list(board.pieces(chess.BISHOP, chess.BLACK))
            )
            if chess.square_rank(sq) != 7
        )
        return float(white_developed - black_developed)
