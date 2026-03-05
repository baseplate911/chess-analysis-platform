"""
Blunder Detector
================
Classifies a chess move as one of:
    "blunder" | "mistake" | "inaccuracy" | "good" | "best"

The primary signal is ``eval_diff`` – the centipawn drop caused by the move
(positive = position worsened).  When a trained blunder_model.pkl is present
the classifier's prediction is used; otherwise a threshold-based heuristic
handles classification.
"""

import os
import logging
from typing import List

import joblib
import numpy as np

logger = logging.getLogger(__name__)

_MODEL_FILE = os.path.join(os.path.dirname(__file__), "blunder_model.pkl")

_LABELS = ["blunder", "mistake", "inaccuracy", "good", "best"]

# eval_diff thresholds (in pawns, positive = worsening)
_THRESHOLDS = [
    (2.0, "blunder"),
    (1.0, "mistake"),
    (0.5, "inaccuracy"),
    (-0.5, "good"),
]


class BlunderDetectorModel:
    """Detects move quality from position features and evaluation difference."""

    def __init__(self, model_path: str = _MODEL_FILE) -> None:
        self.model_path = model_path
        self._clf = None
        self._load_if_exists()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def predict(self, features: List[float], eval_diff: float) -> str:
        """Classify a move given position features and evaluation drop.

        Parameters
        ----------
        features:
            Numeric feature vector describing the position before the move.
        eval_diff:
            Evaluation change caused by the move, in pawns.  Positive values
            indicate the moving side worsened their position.

        Returns
        -------
        One of ``"blunder"``, ``"mistake"``, ``"inaccuracy"``, ``"good"``, ``"best"``.
        """
        if self._clf is not None:
            return self._predict_with_model(features, eval_diff)
        return self._threshold_predict(eval_diff)

    def save(self, path: str = None) -> None:
        """Persist the fitted classifier."""
        if self._clf is None:
            raise RuntimeError("No model loaded or trained – nothing to save.")
        target = path or self.model_path
        joblib.dump(self._clf, target)
        logger.info("BlunderDetectorModel saved to %s", target)

    def load(self, path: str = None) -> None:
        """Load a previously saved classifier."""
        source = path or self.model_path
        self._clf = joblib.load(source)
        logger.info("BlunderDetectorModel loaded from %s", source)

    # ------------------------------------------------------------------
    # Classmethod – stub creation
    # ------------------------------------------------------------------

    @classmethod
    def create_stub_model(cls, save_path: str = _MODEL_FILE) -> "BlunderDetectorModel":
        """Create a RandomForestClassifier stub trained on synthetic data.

        Returns a ready-to-use BlunderDetectorModel instance.
        """
        from sklearn.ensemble import RandomForestClassifier

        rng = np.random.default_rng(42)
        n_samples = 3000
        n_features = 16

        X_pos = rng.normal(0, 1, (n_samples, n_features))
        eval_diff = rng.normal(0, 1.5, (n_samples, 1))
        X = np.hstack([X_pos, eval_diff])

        # Labels derived from eval_diff thresholds
        y = np.array([_threshold_label(d[0]) for d in eval_diff])

        clf = RandomForestClassifier(n_estimators=50, random_state=42)
        clf.fit(X, y)

        instance = cls.__new__(cls)
        instance.model_path = save_path
        instance._clf = clf
        instance.save(save_path)
        logger.info("Stub BlunderDetectorModel created and saved to %s", save_path)
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

    def _predict_with_model(self, features: List[float], eval_diff: float) -> str:
        X = np.array(list(features) + [eval_diff], dtype=float).reshape(1, -1)
        return str(self._clf.predict(X)[0])

    @staticmethod
    def _threshold_predict(eval_diff: float) -> str:
        return _threshold_label(eval_diff)


def _threshold_label(eval_diff: float) -> str:
    """Return move-quality label based purely on evaluation drop."""
    for threshold, label in _THRESHOLDS:
        if eval_diff > threshold:
            return label
    return "best"
