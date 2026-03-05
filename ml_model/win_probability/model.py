"""
Win Probability Predictor
=========================
Predicts the probability of white win / draw / black win given a numeric
feature vector whose first element is the material balance in centipawns.

If a trained model file (chess_win_model.pkl) is present it will be used
directly; otherwise a sigmoid-based heuristic is applied.
"""

import math
import os
import logging
from typing import List

import joblib
import numpy as np

logger = logging.getLogger(__name__)

_MODEL_FILE = os.path.join(os.path.dirname(__file__), "chess_win_model.pkl")


class WinProbabilityModel:
    """Predicts win / draw / black-win probabilities for a chess position."""

    def __init__(self, model_path: str = _MODEL_FILE) -> None:
        self.model_path = model_path
        self._clf = None
        self._load_if_exists()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def predict(self, features: List[float]) -> dict:
        """Return win-probability distribution for the given feature vector.

        Parameters
        ----------
        features:
            Numeric feature vector.  ``features[0]`` must be the material
            balance in centipawns (positive = white ahead).

        Returns
        -------
        dict with keys ``"white_win"``, ``"draw"``, ``"black_win"`` – each a
        float in [0, 1] that sum to 1.
        """
        if self._clf is not None:
            return self._predict_with_model(features)
        return self._heuristic_predict(features)

    def save(self, path: str = None) -> None:
        """Persist the fitted classifier to *path* (defaults to model_path)."""
        if self._clf is None:
            raise RuntimeError("No model loaded or trained – nothing to save.")
        target = path or self.model_path
        joblib.dump(self._clf, target)
        logger.info("WinProbabilityModel saved to %s", target)

    def load(self, path: str = None) -> None:
        """Load a previously saved classifier from *path*."""
        source = path or self.model_path
        self._clf = joblib.load(source)
        logger.info("WinProbabilityModel loaded from %s", source)

    # ------------------------------------------------------------------
    # Classmethod – stub creation
    # ------------------------------------------------------------------

    @classmethod
    def create_stub_model(cls, save_path: str = _MODEL_FILE) -> "WinProbabilityModel":
        """Create a stub MLPClassifier trained on synthetic data and save it.

        The synthetic dataset simulates positions parameterised by 16 features
        (matching FeatureExtractor output).  Labels are derived from material
        balance so the stub is at least directionally sensible.

        Returns a ready-to-use WinProbabilityModel instance.
        """
        from sklearn.neural_network import MLPClassifier

        rng = np.random.default_rng(42)
        n_samples = 2000
        n_features = 16

        # Feature matrix: random positions
        X = rng.normal(0, 1, (n_samples, n_features))
        # material_balance lives in feature[0], scaled to ±8 pawns
        X[:, 0] = rng.normal(0, 300, n_samples)

        # Labels: 0=black win, 1=draw, 2=white win – driven by material balance
        material = X[:, 0]
        white_prob = 1 / (1 + np.exp(-material / 400))
        rand = rng.random(n_samples)
        y = np.where(rand < white_prob * 0.6, 2,
                     np.where(rand < white_prob * 0.6 + 0.25, 1, 0))

        clf = MLPClassifier(
            hidden_layer_sizes=(64, 32),
            max_iter=300,
            random_state=42,
        )
        clf.fit(X, y)

        instance = cls.__new__(cls)
        instance.model_path = save_path
        instance._clf = clf
        instance.save(save_path)
        logger.info("Stub WinProbabilityModel created and saved to %s", save_path)
        return instance

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_if_exists(self) -> None:
        if os.path.exists(self.model_path):
            try:
                self.load(self.model_path)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Could not load model from %s: %s", self.model_path, exc)
                self._clf = None

    def _predict_with_model(self, features: List[float]) -> dict:
        X = np.array(features, dtype=float).reshape(1, -1)
        proba = self._clf.predict_proba(X)[0]
        classes = list(self._clf.classes_)
        # classes are 0=black win, 1=draw, 2=white win
        proba_map = {c: p for c, p in zip(classes, proba)}
        return {
            "white_win": float(proba_map.get(2, 0.0)),
            "draw": float(proba_map.get(1, 0.0)),
            "black_win": float(proba_map.get(0, 0.0)),
        }

    @staticmethod
    def _heuristic_predict(features: List[float]) -> dict:
        """Sigmoid heuristic using material balance (features[0], centipawns)."""
        material_balance = float(features[0]) if features else 0.0
        white_win = 1.0 / (1.0 + math.exp(-material_balance / 400.0))
        # Distribute remainder between draw and black_win
        remainder = 1.0 - white_win
        draw = remainder * 0.4
        black_win = remainder * 0.6
        return {
            "white_win": white_win,
            "draw": draw,
            "black_win": black_win,
        }
