# Win Probability Model (LSTM)

This module uses a fine-tuned **LSTM** model for chess game outcome prediction.

## Architecture

- Move-sequence input (max 100 moves)
- Embedding layer (64 dims)
- LSTM layer (128 units)
- Numeric input: `white_elo`, `black_elo`, `material`
- Dense fusion layers
- Softmax output with 3 classes:
  - `white_win`
  - `black_win`
  - `draw`

## Performance

- Test accuracy: **90.43%**
- Train accuracy: **91.24%**
- Validation accuracy: **90.75%**
- White wins recall: **92.26%**
- Black wins recall: **94.41%**

## Training Data

- Total games: **171,332**
  - 121,332 original games
  - 50,000 fine-tuning games

## Required Assets

- `final_lstm_model_finetuned.h5` (model weights)
- `move_to_idx.pkl` (move vocabulary, 7,340 unique moves)
- `scaler.pkl` (numeric feature scaler)
- `model_metadata.json` (metadata/performance)

## Usage

```python
from ml_model.win_probability.model import WinProbabilityModel

model = WinProbabilityModel()

# Backward-compatible input (old API shape)
result = model.predict([35.0] + [0.0] * 15)

# LSTM-rich input (recommended)
result = model.predict({
    "move_sequence": ["e4", "e5", "Nf3", "Nc6"],
    "white_elo": 1800,
    "black_elo": 1750,
    "material": 15,
})
```

Output format:

```python
{"white_win": float, "black_win": float, "draw": float}
```
