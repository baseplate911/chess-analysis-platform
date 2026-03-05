"""
Player Behaviour Classifier – Training Script
==============================================
Generates synthetic player-statistics training data, fits a
RandomForestClassifier, evaluates it, and saves the model to
player_behaviour_model.pkl.

Usage
-----
    python train.py

To train on real Lichess data, see the project README.md.
"""

import os
import logging

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

_MODEL_FILE = os.path.join(os.path.dirname(__file__), "player_behaviour_model.pkl")

_FEATURE_KEYS = [
    "avg_pieces_traded",
    "attack_frequency",
    "avg_game_length",
    "opening_diversity",
    "king_safety_preference",
    "pawn_advance_frequency",
]

_STYLES = ["Aggressive", "Defensive", "Tactical", "Positional"]


def _heuristic_label(stats: dict) -> str:
    attack = stats["attack_frequency"]
    pieces_traded = stats["avg_pieces_traded"]
    game_length = stats["avg_game_length"]
    king_safety = stats["king_safety_preference"]

    if attack > 0.6 and pieces_traded > 8:
        return "Aggressive"
    if king_safety > 0.7 and game_length > 55:
        return "Defensive"
    if attack > 0.4 and pieces_traded > 5:
        return "Tactical"
    return "Positional"


def generate_synthetic_data(n_samples: int = 4000, seed: int = 42):
    """Produce synthetic (features, label) pairs for player style classification."""
    rng = np.random.default_rng(seed)

    # Generate balanced samples per style
    per_class = n_samples // 4
    rows = []

    # Aggressive: high attack, high piece trades, shorter games
    agg = np.column_stack([
        rng.uniform(9, 15, per_class),   # avg_pieces_traded
        rng.uniform(0.6, 1.0, per_class), # attack_frequency
        rng.uniform(20, 45, per_class),   # avg_game_length
        rng.uniform(0, 1, per_class),     # opening_diversity
        rng.uniform(0, 0.4, per_class),   # king_safety_preference
        rng.uniform(0.2, 0.5, per_class), # pawn_advance_frequency
    ])
    rows.append((agg, ["Aggressive"] * per_class))

    # Defensive: low attack, high king safety, longer games
    dfn = np.column_stack([
        rng.uniform(0, 6, per_class),
        rng.uniform(0, 0.35, per_class),
        rng.uniform(55, 80, per_class),
        rng.uniform(0, 0.5, per_class),
        rng.uniform(0.7, 1.0, per_class),
        rng.uniform(0.1, 0.3, per_class),
    ])
    rows.append((dfn, ["Defensive"] * per_class))

    # Tactical: medium-high attack, moderate piece trades
    tac = np.column_stack([
        rng.uniform(5, 9, per_class),
        rng.uniform(0.4, 0.6, per_class),
        rng.uniform(30, 55, per_class),
        rng.uniform(0.3, 0.8, per_class),
        rng.uniform(0.3, 0.6, per_class),
        rng.uniform(0.1, 0.4, per_class),
    ])
    rows.append((tac, ["Tactical"] * per_class))

    # Positional: low attack, low trades, longer games, high opening diversity
    pos = np.column_stack([
        rng.uniform(0, 5, per_class),
        rng.uniform(0, 0.4, per_class),
        rng.uniform(40, 70, per_class),
        rng.uniform(0.5, 1.0, per_class),
        rng.uniform(0.2, 0.6, per_class),
        rng.uniform(0.05, 0.25, per_class),
    ])
    rows.append((pos, ["Positional"] * per_class))

    X = np.vstack([r[0] for r in rows])
    y = np.concatenate([r[1] for r in rows])

    # Shuffle
    idx = rng.permutation(len(X))
    return X[idx], y[idx]


def train(n_samples: int = 4000) -> RandomForestClassifier:
    """Train and return a fitted RandomForestClassifier."""
    logger.info("Generating %d synthetic training samples …", n_samples)
    X, y = generate_synthetic_data(n_samples)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    logger.info("Training RandomForestClassifier …")
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    logger.info("Test accuracy: %.4f", acc)
    print(f"Test accuracy: {acc:.4f}")
    print(classification_report(y_test, y_pred, target_names=sorted(set(y_test))))
    return clf


def main() -> None:
    clf = train()
    joblib.dump(clf, _MODEL_FILE)
    logger.info("Model saved to %s", _MODEL_FILE)
    print(f"Model saved to {_MODEL_FILE}")


if __name__ == "__main__":
    main()
