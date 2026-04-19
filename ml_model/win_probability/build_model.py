"""
Build LSTM model architecture locally to avoid deserialization issues.
"""

import tensorflow as tf
from tensorflow.keras.layers import Input, Embedding, LSTM, Dense, Concatenate
from tensorflow.keras.models import Model


def build_lstm_model(vocab_size=7341, embedding_dim=64, lstm_units=128, max_seq_length=100):
    """
    Build the LSTM chess prediction model.
    
    Parameters:
    -----------
    vocab_size: int
        Number of unique moves
    embedding_dim: int
        Embedding dimension
    lstm_units: int
        LSTM units
    max_seq_length: int
        Maximum sequence length
    
    Returns:
    --------
    model: Functional Keras model
    """
    
    # Input 1: Move sequence
    move_sequence = Input(shape=(max_seq_length,), dtype='int32', name='move_sequence')
    
    # Embedding layer
    x1 = Embedding(
        input_dim=vocab_size,
        output_dim=embedding_dim,
        mask_zero=True,
        name='embedding'
    )(move_sequence)
    
    # LSTM layer
    x1 = LSTM(lstm_units, return_sequences=False, name='lstm')(x1)
    
    # Input 2: Numeric features (white_elo, black_elo, material)
    numeric_features = Input(shape=(3,), dtype='float32', name='numeric_features')
    
    # Concatenate
    x = Concatenate()([x1, numeric_features])
    
    # Dense layers
    x = Dense(64, activation='relu', name='dense1')(x)
    x = Dense(32, activation='relu', name='dense2')(x)
    
    # Output layer (3 classes: white win, black win, draw)
    output = Dense(3, activation='softmax', name='output')(x)
    
    # Create model
    model = Model(inputs=[move_sequence, numeric_features], outputs=output)
    
    return model


if __name__ == "__main__":
    # Test
    model = build_lstm_model()
    model.summary()
    print("✅ Model built successfully!")