"""
Blunder Detector
================
Classifies a chess move as one of:
    "Brilliant" | "Great" | "Good" | "Inaccuracy" | "Mistake" | "Blunder"

Uses an XGBoost classifier trained on 709,561 Lichess moves.  When the
pre-trained model files are present the XGBoost prediction is returned;
otherwise a threshold-based heuristic handles classification.

Model files expected at (relative to this file):
    chess_xgboost_model.json  – XGBoost native model
    label_map.json            – maps integer-encoded labels → string names
    features.json             – ordered list of the 14 feature names
"""

import json
import os
import logging
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

_DIR = os.path.dirname(__file__)
_XGBOOST_MODEL_FILE = os.path.join(_DIR, "chess_xgboost_model.json")
_LABEL_MAP_FILE = os.path.join(_DIR, "label_map.json")
_FEATURES_FILE = os.path.join(_DIR, "features.json")

# The 14 features consumed by the XGBoost model (order matters)
FEATURES = [
    "move_number", "color",
    "eval_before", "eval_after",
    "is_capture", "is_check", "is_checkmate", "is_castling",
    "is_en_passant", "piece_type", "promotion",
    "clock_before", "clock_after", "time_spent",
]

# eval_diff thresholds (in pawns, positive = worsening) used as fallback
_THRESHOLDS = [
    (2.0, "Blunder"),
    (1.0, "Mistake"),
    (0.5, "Inaccuracy"),
    (-0.5, "Good"),
    (-1.5, "Great"),
]


class XGBoostMoveClassifier:
    """Classifies chess moves using an XGBoost model trained on Lichess data.

    Falls back to a threshold heuristic when model files are not present.
    """

    def __init__(
        self,
        model_path: str = _XGBOOST_MODEL_FILE,
        label_map_path: str = _LABEL_MAP_FILE,
        features_path: str = _FEATURES_FILE,
    ) -> None:
        self.model_path = model_path
        self.label_map_path = label_map_path
        self.features_path = features_path

        self._clf = None
        self._label_map: Optional[Dict[int, str]] = None
        self._features: List[str] = FEATURES

        self._load_if_exists()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def predict(self, features_dict: Dict[str, float]) -> str:
        """Classify a move given a dict of the 14 feature values.

        Parameters
        ----------
        features_dict:
            Dict with the 14 feature keys defined in ``FEATURES``.

        Returns
        -------
        One of ``"Brilliant"``, ``"Great"``, ``"Good"``, ``"Inaccuracy"``,
        ``"Mistake"``, ``"Blunder"``.
        """
        if self._clf is not None:
            return self._predict_with_model(features_dict)
        return self._threshold_predict(features_dict)

    def predict_proba(self, features_dict: Dict[str, float]) -> Dict[str, float]:
        """Return a dict mapping each label to its predicted probability.

        Falls back to a degenerate distribution (1.0 on the predicted class)
        when the XGBoost model is unavailable.
        """
        if self._clf is not None:
            x = self._build_array(features_dict)
            proba = self._clf.predict_proba(x)[0]
            labels = self._get_labels()
            return {label: float(p) for label, p in zip(labels, proba)}
        # Fallback: degenerate distribution
        label = self._threshold_predict(features_dict)
        all_labels = ["Brilliant", "Great", "Good", "Inaccuracy", "Mistake", "Blunder"]
        return {l: (1.0 if l == label else 0.0) for l in all_labels}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_if_exists(self) -> None:
        """Load the XGBoost model and supporting JSON files if they exist."""
        if not os.path.exists(self.model_path):
            logger.info(
                "XGBoost model file not found at %s – using threshold heuristic.",
                self.model_path,
            )
            return

        try:
            import xgboost as xgb  # noqa: PLC0415

            clf = xgb.XGBClassifier()
            clf.load_model(self.model_path)
            self._clf = clf
            logger.info("XGBoostMoveClassifier loaded from %s", self.model_path)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not load XGBoost model from %s: %s", self.model_path, exc)
            self._clf = None
            return

        # Load label map
        if os.path.exists(self.label_map_path):
            try:
                with open(self.label_map_path, "r", encoding="utf-8") as fh:
                    raw = json.load(fh)
                # Keys may be strings in JSON; convert to int
                self._label_map = {int(k): v for k, v in raw.items()}
            except Exception as exc:  # noqa: BLE001
                logger.warning("Could not load label map from %s: %s", self.label_map_path, exc)

        # Load feature list
        if os.path.exists(self.features_path):
            try:
                with open(self.features_path, "r", encoding="utf-8") as fh:
                    self._features = json.load(fh)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Could not load features from %s: %s", self.features_path, exc)

    def _build_array(self, features_dict: Dict[str, float]) -> np.ndarray:
        """Convert a feature dict to a numpy array in the correct feature order."""
        return np.array(
            [float(features_dict.get(f, 0.0)) for f in self._features],
            dtype=float,
        ).reshape(1, -1)

    def _get_labels(self) -> List[str]:
        """Return the ordered list of label names for the classifier."""
        if self._label_map:
            return [self._label_map[i] for i in sorted(self._label_map.keys())]
        return ["Brilliant", "Great", "Good", "Inaccuracy", "Mistake", "Blunder"]

    def _predict_with_model(self, features_dict: Dict[str, float]) -> str:
        x = self._build_array(features_dict)
        raw = int(self._clf.predict(x)[0])
        if self._label_map and raw in self._label_map:
            return self._label_map[raw]
        labels = self._get_labels()
        if 0 <= raw < len(labels):
            return labels[raw]
        return str(raw)

    @staticmethod
    def _threshold_predict(features_dict: Dict[str, float]) -> str:
        eval_before = float(features_dict.get("eval_before", 0.0))
        eval_after = float(features_dict.get("eval_after", 0.0))
        eval_diff = eval_before - eval_after
        return _threshold_label(eval_diff)


# ---------------------------------------------------------------------------
# Backward-compatible alias
# ---------------------------------------------------------------------------

BlunderDetectorModel = XGBoostMoveClassifier


def _threshold_label(eval_diff: float) -> str:
    """Return move-quality label based purely on evaluation drop."""
    for threshold, label in _THRESHOLDS:
        if eval_diff > threshold:
            return label
    return "Brilliant"
