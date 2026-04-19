"""Machine-learning service for win-probability prediction and player style classification."""

import math
import os
from typing import Dict, List
import pickle

try:
    import joblib
    import numpy as np
    from tensorflow.keras.models import load_model
    _NUMPY_AVAILABLE = True
    _LSTM_AVAILABLE = True
except ImportError:
    _NUMPY_AVAILABLE = False
    _LSTM_AVAILABLE = False


class MLService:
    """Loads LSTM model + supporting files for predictions."""

    MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "ml_model", "win_probability")

    def __init__(self):
        self.lstm_model = None
        self.scaler = None
        self.move_to_idx = None
        self.load_models()

    # ------------------------------------------------------------------
    # Model loading
    # ------------------------------------------------------------------

    def load_models(self) -> None:
        """Load LSTM model and supporting files."""
        if _LSTM_AVAILABLE:
            self._load_lstm()
        self._load_supporting_files()

    def _load_lstm(self) -> None:
        """Load LSTM model from .keras file."""
        model_path = os.path.join(self.MODEL_DIR, "final_lstm_model.keras")
        
        if not os.path.exists(model_path):
            print(f"[LSTM] Model not found: {model_path}")
            return
        
        try:
            self.lstm_model = load_model(model_path)
            print(f"[LSTM] Model loaded! (90.43% accuracy)")
        except Exception as e:
            print(f"[LSTM] Failed to load: {e}")

    def _load_supporting_files(self) -> None:
        """Load scaler and move mapping."""
        # Scaler
        scaler_path = os.path.join(self.MODEL_DIR, "scaler.pkl")
        if os.path.exists(scaler_path):
            try:
                with open(scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                print(f"[LSTM] Scaler loaded!")
            except Exception as e:
                print(f"[LSTM] Scaler error: {e}")
        
        # Move mapping
        move_path = os.path.join(self.MODEL_DIR, "move_to_idx.pkl")
        if os.path.exists(move_path):
            try:
                with open(move_path, 'rb') as f:
                    self.move_to_idx = pickle.load(f)
                print(f"[LSTM] Move mapping loaded! ({len(self.move_to_idx)} moves)")
            except Exception as e:
                print(f"[LSTM] Move mapping error: {e}")

    # ------------------------------------------------------------------
    # Public prediction API
    # ------------------------------------------------------------------

    def predict_win_probability(self, features: List[float]) -> List[float]:
        """Predict [white_win, draw, black_win] probabilities.
        
        Uses LSTM model when available, otherwise falls back to sigmoid heuristic.
        """
        if self.lstm_model is not None and self.scaler is not None and _NUMPY_AVAILABLE:
            try:
                # Prepare inputs for LSTM
                X_moves = np.zeros((1, 100), dtype='int32')  # Empty move sequence
                X_numeric = np.array([[1600, 1600, features[0] if features else 0]], dtype='float32')
                X_numeric_scaled = self.scaler.transform(X_numeric)
                
                # LSTM prediction
                prediction = self.lstm_model.predict([X_moves, X_numeric_scaled], verbose=0)
                proba = prediction[0].tolist()
                
                return [proba[0], proba[2], proba[1]]
            except Exception as e:
                print(f"[LSTM] Prediction error: {e}")
        
        # Fallback
        return self._sigmoid_win_probability(features[0] if features else 0.0)

    def classify_move_quality(self, features: List[float], eval_diff: float) -> str:
        """Classify a move as blunder/mistake/inaccuracy/good/best."""
        return self._threshold_move_quality(eval_diff)

    def classify_player_style(self, player_stats: Dict) -> str:
        """Classify a player's style from accuracy."""
        return self._heuristic_player_style(player_stats)

    # ------------------------------------------------------------------
    # Heuristic fallbacks
    # ------------------------------------------------------------------

    @staticmethod
    def _sigmoid_win_probability(cp_eval: float) -> List[float]:
        """Convert centipawn evaluation to win/draw/loss probabilities."""
        white_prob = 1.0 / (1.0 + math.exp(-cp_eval / 4.0))
        draw_prob = 0.3 * (1.0 - abs(white_prob - 0.5) * 2.0)
        draw_prob = max(0.0, draw_prob)
        black_prob = max(0.0, 1.0 - white_prob - draw_prob)
        total = white_prob + draw_prob + black_prob
        return [white_prob / total, draw_prob / total, black_prob / total]

    @staticmethod
    def _threshold_move_quality(eval_diff: float) -> str:
        """Classify move quality from evaluation delta."""
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
        """Derive playing style from accuracy statistics."""
        accuracy = float(player_stats.get("accuracy", 0.0))
        if accuracy >= 90:
            return "positional"
        if accuracy >= 75:
            return "balanced"
        if accuracy >= 60:
            return "aggressive"
        return "defensive"