"""
Chess Win Probability Predictor Module
======================================

This module provides LSTM-based prediction of chess game outcomes
(white win, draw, or black win) based on move sequences and player ratings.
"""

from .model import WinProbabilityModel

__all__ = ['WinProbabilityModel']