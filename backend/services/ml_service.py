"""Machine-learning service for win-probability prediction and player style classification."""

import math
import os
from typing import Dict, List

try:
    import joblib
    import numpy as np
    _NUMPY_AVAILABLE = True
except ImportError:
    _NUMPY_AVAILABLE = False


class MLService:
    """Loads trained models (if present) and provides prediction capabilities.

    When model files are absent the service falls back to deterministic heuristics
    so that the application remains fully functional without pre-trained artefacts.
    """

    MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")

    def __init__(self):
        self.win_prob_model = None
        self.move_quality_model = None
        self.player_style_model = None
        self.load_models()

    # ------------------------------------------------------------------
    # Model loading
    # ------------------------------------------------------------------

    def load_models(self) -> None:
        """Try to load serialised sklearn models from the models/ directory.

        Falls back to stub implementations when files are not found.
        """
        if not _NUMPY_AVAILABLE:
            return

        for attr, filename in [
            ("win_prob_model", "win_prob_model.pkl"),
            ("move_quality_model", "move_quality_model.pkl"),
            ("player_style_model", "player_style_model.pkl"),
        ]:
            path = os.path.join(self.MODEL_DIR, filename)
            if os.path.exists(path):
                try:
                    setattr(self, attr, joblib.load(path))
                except Exception:
                    pass  # Keep attribute as None; will use heuristic fallback

    # ------------------------------------------------------------------
    # Public prediction API
    # ------------------------------------------------------------------

    def predict_win_probability(self, features: List[float]) -> List[float]:
        """Predict [white_win, draw, black_win] probabilities for a given feature vector.

        Uses a trained model when available, otherwise applies a sigmoid heuristic
        based on the material-balance feature (index 0).
        """
        if self.win_prob_model is not None and _NUMPY_AVAILABLE:
            try:
                x = np.array(features).reshape(1, -1)
                proba = self.win_prob_model.predict_proba(x)[0].tolist()
                # Ensure exactly three classes
                if len(proba) == 3:
                    return proba
            except Exception:
                pass

        return self._sigmoid_win_probability(features[0] if features else 0.0)

    def classify_move_quality(self, features: List[float], eval_diff: float) -> str:
        """Classify a move as blunder/mistake/inaccuracy/good/best.

        Uses a trained model when available, otherwise applies the eval_diff thresholds.
        eval_diff should be positive when the position worsened (eval_before - eval_after).
        """
        if self.move_quality_model is not None and _NUMPY_AVAILABLE:
            try:
                x = np.array(features + [eval_diff]).reshape(1, -1)
                return str(self.move_quality_model.predict(x)[0])
            except Exception:
                pass

        return self._threshold_move_quality(eval_diff)

    def classify_player_style(self, player_stats: Dict) -> str:
        """Classify a player's style (aggressive/positional/defensive/balanced).

        Uses a trained model when available, otherwise derives style from accuracy.
        """
        if self.player_style_model is not None and _NUMPY_AVAILABLE:
            try:
                accuracy = float(player_stats.get("accuracy", 0.0))
                total_games = float(player_stats.get("total_games", 0))
                x = np.array([[accuracy, total_games]])
                return str(self.player_style_model.predict(x)[0])
            except Exception:
                pass

        return self._heuristic_player_style(player_stats)

    # ------------------------------------------------------------------
    # Heuristic fallbacks
    # ------------------------------------------------------------------

    @staticmethod
    def _sigmoid_win_probability(cp_eval: float) -> List[float]:
        """Convert a centipawn (pawns) evaluation to win/draw/loss probabilities.

        Formula:
            white_prob = sigmoid(cp_eval / 4)   (scaled so ±1 pawn ≈ 56 % / 44 %)
            draw_prob  = 0.3 * (1 - |white_prob - 0.5| * 2)
            black_prob = 1 - white_prob - draw_prob
        """
        white_prob = 1.0 / (1.0 + math.exp(-cp_eval / 4.0))
        draw_prob = 0.3 * (1.0 - abs(white_prob - 0.5) * 2.0)
        draw_prob = max(0.0, draw_prob)
        black_prob = max(0.0, 1.0 - white_prob - draw_prob)
        # Re-normalise to ensure they sum to 1
        total = white_prob + draw_prob + black_prob
        return [white_prob / total, draw_prob / total, black_prob / total]

    @staticmethod
    def _threshold_move_quality(eval_diff: float) -> str:
        """Classify move quality from evaluation delta.

        eval_diff is positive when the position worsened (eval_before - eval_after).
        """
        if eval_diff > 2.0:
            return "blunder"
        if eval_diff > 1.0:
            return "mistake"
        if eval_diff > 0.5:
            return "inaccuracy"
        if eval_diff > -0.5:
            return "good"
        return "best"

    @staticmethod
    def _heuristic_player_style(player_stats: Dict) -> str:
        """Derive a rough playing style from accuracy statistics."""
        accuracy = float(player_stats.get("accuracy", 0.0))
        if accuracy >= 90:
            return "positional"
        if accuracy >= 75:
            return "balanced"
        if accuracy >= 60:
            return "aggressive"
        return "defensive"
