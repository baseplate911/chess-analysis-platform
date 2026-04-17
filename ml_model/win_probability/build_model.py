"""LSTM architecture builder for win-probability prediction."""

from __future__ import annotations

from typing import Any

from ml_model.win_probability.constants import MAX_MOVES, NUMERIC_FEATURES

try:
    import tensorflow as tf
except ImportError:
    tf = None

EMBEDDING_DIM = 64
LSTM_UNITS = 128
OUTPUT_CLASSES = 3  # white_win, black_win, draw


def build_lstm_win_probability_model(vocab_size: int) -> Any:
    """Build and return the two-input LSTM classifier model."""
    if tf is None:
        raise RuntimeError("TensorFlow is not available; cannot build LSTM model.")

    move_input = tf.keras.Input(shape=(MAX_MOVES,), name="move_sequence")
    x = tf.keras.layers.Embedding(
        input_dim=vocab_size,
        output_dim=EMBEDDING_DIM,
        mask_zero=True,
        name="move_embedding",
    )(move_input)
    x = tf.keras.layers.LSTM(LSTM_UNITS, name="move_lstm")(x)

    numeric_input = tf.keras.Input(shape=(NUMERIC_FEATURES,), name="numeric_features")
    n = tf.keras.layers.Dense(32, activation="relu", name="numeric_dense")(numeric_input)

    merged = tf.keras.layers.Concatenate(name="fusion")([x, n])
    merged = tf.keras.layers.Dense(64, activation="relu", name="fusion_dense")(merged)
    output = tf.keras.layers.Dense(OUTPUT_CLASSES, activation="softmax", name="prediction")(merged)

    model = tf.keras.Model(inputs=[move_input, numeric_input], outputs=output, name="win_probability_lstm")
    return model
