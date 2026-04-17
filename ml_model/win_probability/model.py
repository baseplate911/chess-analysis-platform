"""
LSTM Win Probability Predictor
==============================
Predicts white-win / black-win / draw probabilities from move sequences and
numeric features. If model assets are missing, falls back to a material-based
heuristic so the API remains available.
"""

from __future__ import annotations

import json
import logging
import math
import os
import pickle
from typing import Any, Dict, List, Sequence, Tuple

import numpy as np

try:
    import tensorflow as tf
except ImportError:
    tf = None

from ml_model.win_probability.constants import MAX_MOVES, MIN_VOCAB_SIZE, NUMERIC_FEATURES

logger = logging.getLogger(__name__)

_MODULE_DIR = os.path.dirname(__file__)
_WEIGHTS_FILE = os.path.join(_MODULE_DIR, "final_lstm_model_finetuned.h5")
_MOVE_IDX_FILE = os.path.join(_MODULE_DIR, "move_to_idx.pkl")
_SCALER_FILE = os.path.join(_MODULE_DIR, "scaler.pkl")
_METADATA_FILE = os.path.join(_MODULE_DIR, "model_metadata.json")


class WinProbabilityModel:
    """Predicts win / draw / black-win probabilities for a chess position."""

    def __init__(
        self,
        model_path: str = _WEIGHTS_FILE,
        move_idx_path: str = _MOVE_IDX_FILE,
        scaler_path: str = _SCALER_FILE,
        metadata_path: str = _METADATA_FILE,
    ) -> None:
        self.model_path = model_path
        self.move_idx_path = move_idx_path
        self.scaler_path = scaler_path
        self.metadata_path = metadata_path

        self._model = None
        self._move_to_idx: Dict[str, int] = {}
        self._scaler = None
        self.metadata: Dict[str, Any] = {}
        self._load_assets()

    def predict(self, features: Any) -> dict:
        """Return win-probability distribution.

        Backward-compatible inputs:
        - Previous numeric feature vector (list/tuple/ndarray) where index 0 is
          material in centipawns.
        - Dict input with keys: move_sequence, white_elo, black_elo, material.
        """
        moves, white_elo, black_elo, material = self._parse_input(features)

        if self._model is None or self._scaler is None:
            return self._heuristic_predict(material)

        encoded = self._encode_moves(moves)
        numeric = np.array([[white_elo, black_elo, material]], dtype=float)
        scaled_numeric = self._scale_numeric(numeric)
        pred = self._model.predict([encoded, scaled_numeric], verbose=0)[0]

        white_win = float(pred[0])
        black_win = float(pred[1])
        draw = float(pred[2])
        total = white_win + black_win + draw
        if total <= 0:
            return self._heuristic_predict(material)
        return {
            "white_win": white_win / total,
            "black_win": black_win / total,
            "draw": draw / total,
        }

    def _load_assets(self) -> None:
        self.metadata = self._load_metadata(self.metadata_path)
        self._move_to_idx = self._load_pickle(self.move_idx_path, default={})
        self._scaler = self._load_pickle(self.scaler_path, default=None)

        if tf is None:
            logger.warning("TensorFlow is unavailable; using heuristic win-probability fallback.")
            return
        if not self._move_to_idx:
            logger.warning("Move encoder not found/empty at %s; using heuristic fallback.", self.move_idx_path)
            return
        if self._scaler is None:
            logger.warning("Numeric scaler not found at %s; using heuristic fallback.", self.scaler_path)
            return
        if not os.path.exists(self.model_path):
            logger.warning("LSTM weight file not found at %s; using heuristic fallback.", self.model_path)
            return

        try:
            from ml_model.win_probability.build_model import build_lstm_win_probability_model

            vocab_size = max(self._move_to_idx.values(), default=0) + 1
            self._model = build_lstm_win_probability_model(vocab_size=max(vocab_size, MIN_VOCAB_SIZE))
            self._model.load_weights(self.model_path)
            logger.info("Loaded LSTM win-probability weights from %s", self.model_path)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not load LSTM model weights from %s: %s", self.model_path, exc)
            self._model = None

    @staticmethod
    def _load_pickle(path: str, default: Any) -> Any:
        try:
            with open(path, "rb") as f:
                return pickle.load(f)
        except Exception:  # noqa: BLE001
            return default

    @staticmethod
    def _load_metadata(path: str) -> Dict[str, Any]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:  # noqa: BLE001
            return {}

    @staticmethod
    def _parse_input(features: Any) -> Tuple[Sequence[str], float, float, float]:
        if isinstance(features, dict):
            moves = features.get("move_sequence") or []
            white_elo = float(features.get("white_elo", 1500))
            black_elo = float(features.get("black_elo", 1500))
            material = float(features.get("material", 0))
            return moves, white_elo, black_elo, material

        if isinstance(features, (list, tuple, np.ndarray)):
            seq = list(features)
            material = float(seq[0]) if seq else 0.0
            return [], 1500.0, 1500.0, material

        return [], 1500.0, 1500.0, 0.0

    def _encode_moves(self, move_sequence: Sequence[str]) -> np.ndarray:
        unknown_idx = self._move_to_idx.get("<UNK>", 0)
        encoded_seq = [self._move_to_idx.get(move, unknown_idx) for move in move_sequence]
        if len(encoded_seq) < MAX_MOVES:
            encoded_seq += [0] * (MAX_MOVES - len(encoded_seq))
        else:
            encoded_seq = encoded_seq[:MAX_MOVES]
        return np.array([encoded_seq], dtype=np.int32)

    def _scale_numeric(self, numeric: np.ndarray) -> np.ndarray:
        if self._scaler is None:
            return numeric
        if hasattr(self._scaler, "transform"):
            return self._scaler.transform(numeric)
        if isinstance(self._scaler, dict):
            mean = np.array(self._scaler.get("mean", [0.0] * NUMERIC_FEATURES), dtype=float)
            scale = np.array(self._scaler.get("scale", [1.0] * NUMERIC_FEATURES), dtype=float)
            scale = np.where(scale == 0, 1.0, scale)
            return (numeric - mean) / scale
        return numeric

    @staticmethod
    def _heuristic_predict(material_balance: float) -> dict:
        """Material-only fallback in centipawns."""
        white_win = 1.0 / (1.0 + math.exp(-material_balance / 400.0))
        remainder = 1.0 - white_win
        draw = remainder * 0.4
        black_win = remainder * 0.6
        return {
            "white_win": white_win,
            "black_win": black_win,
            "draw": draw,
        }
