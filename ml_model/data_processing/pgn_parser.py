"""
PGN Parser
==========
Utilities for parsing PGN (Portable Game Notation) strings into structured
data and extracting aggregate game features.

Requires the ``python-chess`` library.
"""

import re
import logging
from typing import Dict, List

import chess
import chess.pgn
import io

logger = logging.getLogger(__name__)


class PGNParser:
    """Parse PGN strings into move sequences and aggregate game features."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse_pgn(self, pgn_string: str) -> List[Dict]:
        """Parse a PGN string and return per-move records.

        Parameters
        ----------
        pgn_string:
            A single game in PGN format.

        Returns
        -------
        List of dicts, one per half-move (ply), each containing:
            ``fen``         – FEN string *before* the move is played
            ``move``        – UCI string of the move (e.g. ``"e2e4"``)
            ``move_number`` – full-move number
            ``color``       – ``"white"`` or ``"black"``
        """
        game = self._read_game(pgn_string)
        if game is None:
            return []

        records: List[Dict] = []
        board = game.board()

        for node in game.mainline():
            move = node.move
            fen_before = board.fen()
            color = "white" if board.turn == chess.WHITE else "black"
            move_number = board.fullmove_number

            records.append({
                "fen": fen_before,
                "move": move.uci(),
                "move_number": move_number,
                "color": color,
            })
            board.push(move)

        return records

    def extract_game_features(self, pgn_string: str) -> Dict:
        """Return aggregate features for an entire game.

        Returns
        -------
        Dict with keys:
            ``total_moves``     – total number of half-moves played
            ``captures``        – number of capture moves
            ``checks``          – number of moves that result in check
            ``castlings``       – number of castling moves
            ``promotions``      – number of pawn promotions
            ``avg_material``    – average material balance over all positions
            ``opening_moves``   – first 10 moves as a list of UCI strings
            ``result``          – game result string (``"1-0"``, ``"0-1"``, ``"1/2-1/2"``, ``"*"``)
            ``white_player``    – value of White header tag (or empty string)
            ``black_player``    – value of Black header tag (or empty string)
        """
        game = self._read_game(pgn_string)
        if game is None:
            return self._empty_features()

        board = game.board()
        total_moves = 0
        captures = 0
        checks = 0
        castlings = 0
        promotions = 0
        material_sum = 0.0
        opening_moves: List[str] = []

        for node in game.mainline():
            move = node.move
            total_moves += 1

            if board.is_capture(move):
                captures += 1
            if board.is_castling(move):
                castlings += 1
            if move.promotion:
                promotions += 1

            board.push(move)

            if board.is_check():
                checks += 1
            if total_moves <= 10:
                opening_moves.append(move.uci())
            material_sum += self._material_balance(board)

        avg_material = material_sum / max(total_moves, 1)

        return {
            "total_moves": total_moves,
            "captures": captures,
            "checks": checks,
            "castlings": castlings,
            "promotions": promotions,
            "avg_material": avg_material,
            "opening_moves": opening_moves,
            "result": game.headers.get("Result", "*"),
            "white_player": game.headers.get("White", ""),
            "black_player": game.headers.get("Black", ""),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _read_game(pgn_string: str):
        """Parse PGN text and return a chess.pgn.Game (or None on failure)."""
        try:
            pgn_io = io.StringIO(pgn_string)
            game = chess.pgn.read_game(pgn_io)
            return game
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to parse PGN: %s", exc)
            return None

    @staticmethod
    def _material_balance(board: chess.Board) -> float:
        """Centipawn material balance (positive = white ahead)."""
        piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 0,
        }
        balance = 0
        for piece_type, value in piece_values.items():
            balance += value * len(board.pieces(piece_type, chess.WHITE))
            balance -= value * len(board.pieces(piece_type, chess.BLACK))
        return float(balance)

    @staticmethod
    def _empty_features() -> Dict:
        return {
            "total_moves": 0,
            "captures": 0,
            "checks": 0,
            "castlings": 0,
            "promotions": 0,
            "avg_material": 0.0,
            "opening_moves": [],
            "result": "*",
            "white_player": "",
            "black_player": "",
        }
