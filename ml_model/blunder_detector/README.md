# Blunder Detector – XGBoost Move Classifier

## Overview

The move classifier is an **XGBoost** model trained on **709,561 real Lichess
moves**.  It replaces the earlier RandomForest stub that was trained on
synthetic data.

---

## Label Classes

The model predicts one of six move-quality categories:

| Label       | Meaning                                      |
|-------------|----------------------------------------------|
| Brilliant   | Exceptional move, objectively the best play  |
| Great       | Very strong move                             |
| Good        | Solid, accurate move                         |
| Inaccuracy  | Slightly suboptimal (eval drop < 0.5 pawns)  |
| Mistake     | Noticeable error (eval drop 0.5–1.0 pawns)   |
| Blunder     | Serious error (eval drop > 1.0 pawns)        |

---

## Features (14 total, in order)

| # | Feature        | Description                                                        |
|---|----------------|--------------------------------------------------------------------|
| 1 | `move_number`  | Half-move counter                                                  |
| 2 | `color`        | 1 = White, 0 = Black                                               |
| 3 | `eval_before`  | Engine evaluation before the move (pawns, from mover's perspective)|
| 4 | `eval_after`   | Engine evaluation after the move (pawns, from mover's perspective) |
| 5 | `is_capture`   | 1 if the move captures a piece                                     |
| 6 | `is_check`     | 1 if the move gives check                                          |
| 7 | `is_checkmate` | 1 if the move delivers checkmate                                   |
| 8 | `is_castling`  | 1 if the move is castling                                          |
| 9 | `is_en_passant`| 1 if the move is en passant                                        |
|10 | `piece_type`   | Integer piece type (PAWN=1, KNIGHT=2, BISHOP=3, ROOK=4, QUEEN=5, KING=6) |
|11 | `promotion`    | 1 if the move is a pawn promotion                                  |
|12 | `clock_before` | Time remaining before move (seconds); defaults to 0.0              |
|13 | `clock_after`  | Time remaining after move (seconds); defaults to 0.0               |
|14 | `time_spent`   | Time spent on this move (seconds); defaults to 0.0                 |

---

## Model Files

The following files are **not** committed to the repository (they are large /
binary artefacts).  Place them in this directory (`ml_model/blunder_detector/`)
before starting the backend:

| File                        | Description                                      |
|-----------------------------|--------------------------------------------------|
| `chess_xgboost_model.json`  | XGBoost model in native JSON format              |
| `label_map.json`            | Maps integer-encoded class indices → label names |
| `features.json`             | Ordered list of the 14 feature names             |

When the files are absent the classifier falls back to a threshold-based
heuristic using the `eval_before`/`eval_after` difference.

---

## Obtaining the Model Files

1. Open the training notebook in Google Colab.
2. Collect Lichess game data and train with XGBoost.
3. Export the artefacts:

```python
model.save_model("chess_xgboost_model.json")

import json
with open("label_map.json", "w") as f:
    json.dump({str(i): label for i, label in enumerate(model.classes_)}, f)

with open("features.json", "w") as f:
    json.dump(feature_columns, f)
```

4. Download the three files from Colab and copy them into
   `ml_model/blunder_detector/`.

---

## Retraining

To retrain the model from scratch:

1. Download a Lichess game database (PGN) from <https://database.lichess.org/>.
2. Parse games and extract the 14 features for every move.
3. Train an `XGBClassifier` on the resulting dataset.
4. Export and place the three model files as described above.
