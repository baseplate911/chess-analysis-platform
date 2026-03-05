"""
Player Behaviour Classifier
============================
Classifies a player's style based on aggregate game statistics into one of:
    "Aggressive" | "Defensive" | "Tactical" | "Positional"

Input dictionary keys (all numeric):
    avg_pieces_traded       – average number of pieces exchanged per game
    attack_frequency        – fraction of moves that are attacking moves
    avg_game_length         – average number of moves per game
    opening_diversity       – unique openings played / total games (0–1)
    king_safety_preference  – 0=castles early, 1=rarely castles
    pawn_advance_frequency  – fraction of moves that advance pawns
"""

import os
import logging
from typing import Dict

import joblib
import numpy as np

logger = logging.getLogger(__name__)

_MODEL_FILE = os.path.join(os.path.dirname(__file__), "player_behaviour_model.pkl")

_STYLE_LABELS = ["Aggressive", "Defensive", "Tactical", "Positional"]

# Ordered list of feature keys consumed by the model
_FEATURE_KEYS = [
    "avg_pieces_traded",
    "attack_frequency",
    "avg_game_length",
    "opening_diversity",
    "king_safety_preference",
    "pawn_advance_frequency",
]


class PlayerBehaviourModel:
    """Classifies a player's overall playing style."""

    def __init__(self, model_path: str = _MODEL_FILE) -> None:
        self.model_path = model_path
        self._clf = None
        self._load_if_exists()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def predict(self, player_stats: Dict[str, float]) -> str:
        """Classify player style from aggregate statistics.

        Parameters
        ----------
        player_stats:
            Dictionary containing the keys listed in ``_FEATURE_KEYS``.
            Missing keys default to 0.

        Returns
        -------
        One of ``"Aggressive"``, ``"Defensive"``, ``"Tactical"``, ``"Positional"``.
        """
        features = [float(player_stats.get(k, 0.0)) for k in _FEATURE_KEYS]
        if self._clf is not None:
            return self._predict_with_model(features)
        return self._heuristic_predict(player_stats)

    def save(self, path: str = None) -> None:
        """Persist the fitted classifier."""
        if self._clf is None:
            raise RuntimeError("No model loaded or trained – nothing to save.")
        target = path or self.model_path
        joblib.dump(self._clf, target)
        logger.info("PlayerBehaviourModel saved to %s", target)

    def load(self, path: str = None) -> None:
        """Load a previously saved classifier."""
        source = path or self.model_path
        self._clf = joblib.load(source)
        logger.info("PlayerBehaviourModel loaded from %s", source)

    # ------------------------------------------------------------------
    # Classmethod – stub creation
    # ------------------------------------------------------------------

    @classmethod
    def create_stub_model(
        cls, save_path: str = _MODEL_FILE
    ) -> "PlayerBehaviourModel":
        """Create a RandomForestClassifier stub trained on synthetic player data.

        Returns a ready-to-use PlayerBehaviourModel instance.
        """
        from sklearn.ensemble import RandomForestClassifier

        rng = np.random.default_rng(42)
        n_samples = 1200
        n_features = len(_FEATURE_KEYS)

        # Synthetic player stats with plausible ranges
        X = np.column_stack([
            rng.uniform(0, 15, n_samples),   # avg_pieces_traded
            rng.uniform(0, 1, n_samples),    # attack_frequency
            rng.uniform(20, 80, n_samples),  # avg_game_length
            rng.uniform(0, 1, n_samples),    # opening_diversity
            rng.uniform(0, 1, n_samples),    # king_safety_preference
            rng.uniform(0, 0.5, n_samples),  # pawn_advance_frequency
        ])

        # Heuristic labels so training data is directionally meaningful
        y = np.array([
            _heuristic_label(dict(zip(_FEATURE_KEYS, row)))
            for row in X
        ])

        clf = RandomForestClassifier(n_estimators=50, random_state=42)
        clf.fit(X, y)

        instance = cls.__new__(cls)
        instance.model_path = save_path
        instance._clf = clf
        instance.save(save_path)
        logger.info(
            "Stub PlayerBehaviourModel created and saved to %s", save_path
        )
        return instance

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_if_exists(self) -> None:
        if os.path.exists(self.model_path):
            try:
                self.load(self.model_path)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Could not load model from %s: %s", self.model_path, exc
                )
                self._clf = None

    def _predict_with_model(self, features) -> str:
        X = np.array(features, dtype=float).reshape(1, -1)
        return str(self._clf.predict(X)[0])

    @staticmethod
    def _heuristic_predict(player_stats: Dict[str, float]) -> str:
        return _heuristic_label(player_stats)


def _heuristic_label(stats: Dict[str, float]) -> str:
    """Simple rule-based fallback style classifier."""
    attack = float(stats.get("attack_frequency", 0))
    pieces_traded = float(stats.get("avg_pieces_traded", 0))
    game_length = float(stats.get("avg_game_length", 40))
    king_safety = float(stats.get("king_safety_preference", 0.5))

    if attack > 0.6 and pieces_traded > 8:
        return "Aggressive"
    if king_safety > 0.7 and game_length > 55:
        return "Defensive"
    if attack > 0.4 and pieces_traded > 5:
        return "Tactical"
    return "Positional"
