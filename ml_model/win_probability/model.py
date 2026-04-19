"""
LSTM Win Probability Predictor
===============================
Predicts the probability of white win / draw / black win using a fine-tuned LSTM model
given a sequence of moves and numeric features (ELO ratings, material balance).
"""

import os
import logging
from typing import List, Dict
import numpy as np
import tensorflow as tf
import pickle
from build_model import build_lstm_model

logger = logging.getLogger(__name__)

_MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
_MODEL_FILE = os.path.join(_MODEL_DIR, "final_lstm_model_finetuned.h5")
_MOVE_IDX_FILE = os.path.join(_MODEL_DIR, "move_to_idx.pkl")
_SCALER_FILE = os.path.join(_MODEL_DIR, "scaler.pkl")


class WinProbabilityModel:
    """Predicts win / draw / black-win probabilities using LSTM model."""

    def __init__(self, 
                 model_path: str = _MODEL_FILE,
                 move_idx_path: str = _MOVE_IDX_FILE,
                 scaler_path: str = _SCALER_FILE) -> None:
        """
        Initialize the LSTM Win Probability Model.
        
        Parameters:
        -----------
        model_path: str
            Path to the trained LSTM model weights (.h5 file)
        move_idx_path: str
            Path to the move_to_idx.pkl encoder
        scaler_path: str
            Path to the feature scaler (StandardScaler)
        """
        self.model_path = model_path
        self.move_idx_path = move_idx_path
        self.scaler_path = scaler_path
        self.model = None
        self.move_to_idx = None
        self.scaler = None
        self._load_if_exists()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def predict(self, features: List[float] = None, 
                move_sequence: List[str] = None,
                white_elo: int = None,
                black_elo: int = None,
                material: int = None) -> Dict[str, float]:
        """
        Return win-probability distribution for the given input.
        
        Can be called in two ways:
        
        1. With move sequence and ELO features:
           predict(move_sequence=['e4', 'e5', ...], 
                   white_elo=1600, black_elo=1400, material=0)
        
        2. With numeric feature vector (backward compatibility):
           predict(features=[material, ...other features...])
        
        Returns:
        --------
        dict with keys "white_win", "draw", "black_win" – each a float in [0, 1]
        that sum to 1.
        """
        
        # If move sequence provided, use LSTM prediction
        if move_sequence is not None:
            if self.model is None:
                logger.warning("Model not loaded. Using heuristic prediction.")
                return self._heuristic_predict([material or 0])
            return self._predict_with_lstm(move_sequence, white_elo or 1600, 
                                          black_elo or 1400, material or 0)
        
        # Otherwise use feature vector
        if features is not None:
            if self.model is None:
                logger.warning("Model not loaded. Using heuristic prediction.")
                return self._heuristic_predict(features)
            return self._predict_with_features(features)
        
        raise ValueError("Either move_sequence or features must be provided")

    def save(self, path: str = None) -> None:
        """Persist the model weights to *path* (defaults to model_path)."""
        if self.model is None:
            raise RuntimeError("No model loaded – nothing to save.")
        target = path or self.model_path
        self.model.save_weights(target)
        logger.info("LSTM model weights saved to %s", target)

    def load(self, path: str = None) -> None:
        """Load a previously saved model from *path*."""
        source = path or self.model_path
        if self.model is None:
            self.model = build_lstm_model()
        self.model.load_weights(source)
        logger.info("LSTM model weights loaded from %s", source)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_if_exists(self) -> None:
        """Load model components if they exist."""
        try:
            # Build model architecture
            self.model = build_lstm_model()
            
            # Load weights
            if os.path.exists(self.model_path):
                self.model.load_weights(self.model_path)
                logger.info("LSTM model weights loaded from %s", self.model_path)
            else:
                logger.warning("Model file not found at %s", self.model_path)
                self.model = None
            
            # Load move encoder
            if os.path.exists(self.move_idx_path):
                with open(self.move_idx_path, 'rb') as f:
                    self.move_to_idx = pickle.load(f)
                logger.info("Move encoder loaded from %s", self.move_idx_path)
            else:
                logger.warning("Move encoder not found at %s", self.move_idx_path)
            
            # Load scaler
            if os.path.exists(self.scaler_path):
                with open(self.scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                logger.info("Scaler loaded from %s", self.scaler_path)
            else:
                logger.warning("Scaler not found at %s", self.scaler_path)
        
        except Exception as exc:
            logger.warning("Could not load model: %s", exc)
            self.model = None
            self.move_to_idx = None
            self.scaler = None

    def _predict_with_lstm(self, move_sequence: List[str], 
                          white_elo: int, black_elo: int, material: int) -> Dict[str, float]:
        """Make prediction using LSTM model with move sequence."""
        
        # Encode moves
        encoded_seq = [self.move_to_idx.get(move, 0) for move in move_sequence]
        
        # Pad or truncate to max_len=100
        max_len = 100
        if len(encoded_seq) < max_len:
            encoded_seq += [0] * (max_len - len(encoded_seq))
        else:
            encoded_seq = encoded_seq[:max_len]
        
        # Prepare inputs
        X_seq = np.array([encoded_seq], dtype='int32')
        X_numeric = np.array([[white_elo, black_elo, material]], dtype='float32')
        
        # Scale numeric features
        X_numeric_scaled = self.scaler.transform(X_numeric)
        
        # Make prediction
        prediction = self.model.predict([X_seq, X_numeric_scaled], verbose=0)[0]
        
        white_win, black_win, draw = prediction
        
        return {
            "white_win": float(white_win),
            "black_win": float(black_win),
            "draw": float(draw),
        }

    def _predict_with_features(self, features: List[float]) -> Dict[str, float]:
        """Make prediction using numeric features only (backward compatibility)."""
        # For backward compatibility, if only features provided,
        # use material balance (features[0]) as move sequence would
        material = float(features[0]) if features else 0.0
        
        # Default ELO ratings
        white_elo = 1600
        black_elo = 1400
        
        return self._predict_with_lstm([], white_elo, black_elo, int(material))

    @staticmethod
    def _heuristic_predict(features: List[float]) -> Dict[str, float]:
        """Sigmoid heuristic using material balance (features[0], centipawns).
        
        Used when model is not available.
        """
        import math
        
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