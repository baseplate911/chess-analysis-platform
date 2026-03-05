"""
Blunder Detector – Training Script
====================================
Generates synthetic training data, fits a RandomForestClassifier, evaluates
it, and saves the model to blunder_model.pkl.

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

_MODEL_FILE = os.path.join(os.path.dirname(__file__), "blunder_model.pkl")

_LABELS = ["blunder", "mistake", "inaccuracy", "good", "best"]
_THRESHOLDS = [
    (2.0, "blunder"),
    (1.0, "mistake"),
    (0.5, "inaccuracy"),
    (-0.5, "good"),
]

_N_POSITION_FEATURES = 16


def _threshold_label(eval_diff: float) -> str:
    for threshold, label in _THRESHOLDS:
        if eval_diff > threshold:
            return label
    return "best"


def generate_synthetic_data(n_samples: int = 8000, seed: int = 42):
    """Produce synthetic (features, label) pairs.

    Feature vector: 16 position features + 1 eval_diff = 17 features.
    """
    rng = np.random.default_rng(seed)

    X_pos = rng.normal(0, 1, (n_samples, _N_POSITION_FEATURES))
    X_pos[:, 0] = rng.normal(0, 300, n_samples)   # material balance

    # eval_diff drawn from a distribution that over-samples interesting cases
    eval_diff = np.concatenate([
        rng.normal(3.0, 0.5, n_samples // 5),    # blunders
        rng.normal(1.5, 0.3, n_samples // 5),    # mistakes
        rng.normal(0.75, 0.15, n_samples // 5),  # inaccuracies
        rng.uniform(-0.5, 0.5, n_samples // 5),  # good
        rng.uniform(-2.0, -0.5, n_samples // 5), # best
    ])
    rng.shuffle(eval_diff)
    eval_diff = eval_diff[:n_samples]

    X = np.hstack([X_pos, eval_diff.reshape(-1, 1)])
    y = np.array([_threshold_label(d) for d in eval_diff])
    return X, y


def train(n_samples: int = 8000) -> RandomForestClassifier:
    """Train and return a fitted RandomForestClassifier."""
    logger.info("Generating %d synthetic training samples …", n_samples)
    X, y = generate_synthetic_data(n_samples)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    logger.info("Training RandomForestClassifier …")
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=12,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    logger.info("Test accuracy: %.4f", acc)
    print(f"Training accuracy: {acc:.4f}")
    print(classification_report(y_test, y_pred, target_names=sorted(set(y_test))))
    return clf


def main() -> None:
    clf = train()
    joblib.dump(clf, _MODEL_FILE)
    logger.info("Model saved to %s", _MODEL_FILE)
    print(f"Model saved to {_MODEL_FILE}")


if __name__ == "__main__":
    main()
