# Chess Analysis Platform – ML Models

Three machine-learning model stubs for analysing chess games, designed to
work alongside the platform's backend API.

---

## Models

### 1. Win Probability Predictor (`win_probability/`)

Predicts the probability of **white win / draw / black win** using a fine-tuned
LSTM over move sequences plus numeric features.

| File | Description |
|---|---|
| `build_model.py` | LSTM architecture builder (Embedding 64 + LSTM 128 + numeric fusion) |
| `model.py` | `WinProbabilityModel` class – loads move encoder/scaler and LSTM weights |
| `README.md` | Model-specific architecture, metrics, and asset requirements |

**Output:** `{"white_win": float, "black_win": float, "draw": float}`

**Performance:** 90.43% test accuracy (171,332 games)

---

### 2. Blunder Detector (`blunder_detector/`)

Classifies a chess move as `blunder`, `mistake`, `inaccuracy`, `good`, or
`best` using the evaluation drop and position features.

| File | Description |
|---|---|
| `model.py` | `BlunderDetectorModel` class – sklearn `RandomForestClassifier` or threshold heuristic |
| `train.py` | Training script – saves `blunder_model.pkl` |

**Threshold fallback (eval_diff in pawns):**

| eval_diff | Label |
|---|---|
| > 2.0 | blunder |
| > 1.0 | mistake |
| > 0.5 | inaccuracy |
| > −0.5 | good |
| ≤ −0.5 | best |

---

### 3. Player Behaviour Classifier (`player_behaviour/`)

Classifies a player's style as `Aggressive`, `Defensive`, `Tactical`, or
`Positional` from aggregate game statistics.

| File | Description |
|---|---|
| `model.py` | `PlayerBehaviourModel` class – sklearn `RandomForestClassifier` or rule heuristic |
| `train.py` | Training script – saves `player_behaviour_model.pkl` |

**Input keys:** `avg_pieces_traded`, `attack_frequency`, `avg_game_length`,
`opening_diversity`, `king_safety_preference`, `pawn_advance_frequency`

---

## Data Processing Utilities

### `data_processing/pgn_parser.py`

`PGNParser` uses the `python-chess` library to parse PGN strings.

```python
from ml_model.data_processing.pgn_parser import PGNParser

parser = PGNParser()
moves = parser.parse_pgn(pgn_string)       # list of {fen, move, move_number, color}
features = parser.extract_game_features(pgn_string)  # aggregate dict
```

### `data_processing/feature_extractor.py`

`FeatureExtractor` converts a `chess.Board` to a 16-float feature vector.

```python
import chess
from ml_model.data_processing.feature_extractor import FeatureExtractor

board = chess.Board()
fe = FeatureExtractor()
features = fe.extract_features(board)       # 16 floats
normalised = fe.normalize_features(features)
```

---

## Quick Start (stub models)

```bash
# Install dependencies
pip install -r requirements.txt

# Train all three models from synthetic data
python ml_model/win_probability/train.py
python ml_model/blunder_detector/train.py
python ml_model/player_behaviour/train.py
```

Or create stubs programmatically:

```python
from ml_model.win_probability.model import WinProbabilityModel
from ml_model.blunder_detector.model import BlunderDetectorModel
from ml_model.player_behaviour.model import PlayerBehaviourModel

WinProbabilityModel.create_stub_model()
BlunderDetectorModel.create_stub_model()
PlayerBehaviourModel.create_stub_model()
```

---

## Training on Real Lichess Data

### 1. Download a Lichess database

Lichess publishes monthly PGN dumps (with Stockfish evaluations) at:

```
https://database.lichess.org/
```

Download a standard-rated games file, for example:

```bash
# Download a monthly PGN (several GB compressed)
wget https://database.lichess.org/standard/lichess_db_standard_rated_2024-01.pgn.zst

# Decompress with zstd
zstd -d lichess_db_standard_rated_2024-01.pgn.zst
```

Evaluation-annotated games (needed for the blunder detector) are available at:

```
https://database.lichess.org/#evals
```

### 2. Preprocess the data

Use `PGNParser` to iterate over games and `FeatureExtractor` to build feature
matrices:

```python
import chess.pgn, io
from ml_model.data_processing.pgn_parser import PGNParser
from ml_model.data_processing.feature_extractor import FeatureExtractor

parser = PGNParser()
fe = FeatureExtractor()

with open("lichess_db_standard_rated_2024-01.pgn") as f:
    while True:
        game = chess.pgn.read_game(f)
        if game is None:
            break
        board = game.board()
        for node in game.mainline():
            features = fe.extract_features(board)
            normalised = fe.normalize_features(features)
            board.push(node.move)
            # collect (normalised, label) pairs …
```

### 3. Retrain models

Replace the synthetic-data generation in each `train.py` with your real
feature matrix and labels, then run:

```bash
# Win-probability uses the LSTM pipeline and weight files in ml_model/win_probability/
# (see ml_model/win_probability/README.md)
python ml_model/blunder_detector/train.py
python ml_model/player_behaviour/train.py
```

The classifier `.pkl` files are written next to the respective `train.py`.
The win-probability model loads:
- `final_lstm_model_finetuned.h5`
- `move_to_idx.pkl`
- `scaler.pkl`
- `model_metadata.json`

---

## Dependencies

```
scikit-learn
numpy
tensorflow
keras
python-chess
```

Install with:

```bash
pip install -r requirements.txt
```
