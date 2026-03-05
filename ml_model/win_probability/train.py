"""
Win Probability Model – Training Script
========================================
Generates synthetic training data, fits an MLPClassifier, evaluates it,
and saves the model to chess_win_model.pkl.

Usage
-----
    python train.py

To train on real Lichess data, see the project README.md.
"""

import os
import sys
import logging

import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

_MODEL_FILE = os.path.join(os.path.dirname(__file__), "chess_win_model.pkl")

# Feature index semantics (must match FeatureExtractor output)
_N_FEATURES = 16


def generate_synthetic_data(n_samples: int = 5000, seed: int = 42):
    """Produce synthetic (features, label) pairs.

    Labels: 0 = black win, 1 = draw, 2 = white win
    """
    rng = np.random.default_rng(seed)

    X = rng.normal(0, 1, (n_samples, _N_FEATURES))
    # Feature 0: material balance in centipawns
    X[:, 0] = rng.normal(0, 300, n_samples)
    # Feature 13: material ratio in [0, 1]
    X[:, 13] = rng.uniform(0.3, 0.7, n_samples)

    material = X[:, 0]
    white_p = 1 / (1 + np.exp(-material / 400))
    rand = rng.random(n_samples)
    y = np.where(rand < white_p * 0.6, 2,
                 np.where(rand < white_p * 0.6 + 0.25, 1, 0))

    return X, y


def train(n_samples: int = 5000) -> MLPClassifier:
    """Train and return a fitted MLPClassifier."""
    logger.info("Generating %d synthetic training samples …", n_samples)
    X, y = generate_synthetic_data(n_samples)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    logger.info("Training MLPClassifier …")
    clf = MLPClassifier(
        hidden_layer_sizes=(128, 64, 32),
        activation="relu",
        max_iter=500,
        random_state=42,
        early_stopping=True,
        validation_fraction=0.1,
        n_iter_no_change=20,
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    logger.info("Test accuracy: %.4f", acc)
    print(f"Training accuracy: {acc:.4f}")
    return clf


def main() -> None:
    clf = train()
    joblib.dump(clf, _MODEL_FILE)
    logger.info("Model saved to %s", _MODEL_FILE)
    print(f"Model saved to {_MODEL_FILE}")


if __name__ == "__main__":
    main()
