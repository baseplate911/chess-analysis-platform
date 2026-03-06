"""Shared move-classification constants and helper.

This module is the single source of truth for how moves are labelled based on
the evaluation change (``eval_diff``).  Both :mod:`services.chess_service` and
:mod:`services.ml_service` import from here so that the thresholds stay in sync.

Threshold table (``eval_diff = eval_before − eval_after``, from the mover's
perspective; a positive value means the position *worsened* for the mover):

    +-----------------+--------------------------------------+
    | Classification  | Condition                            |
    +-----------------+--------------------------------------+
    | blunder         | eval_diff > 2.0                      |
    | mistake         | eval_diff > 1.0                      |
    | inaccuracy      | eval_diff > 0.5                      |
    | good            | eval_diff > −0.5                     |
    | best            | eval_diff ≤ −0.5                     |
    +-----------------+--------------------------------------+
"""

# ------------------------------------------------------------------
# Thresholds (in pawns)
# ------------------------------------------------------------------

BLUNDER_THRESHOLD: float = 2.0
"""Evaluation drop above which a move is classified as a **blunder**."""

MISTAKE_THRESHOLD: float = 1.0
"""Evaluation drop above which a move is classified as a **mistake**."""

INACCURACY_THRESHOLD: float = 0.5
"""Evaluation drop above which a move is classified as an **inaccuracy**."""

GOOD_THRESHOLD: float = -0.5
"""Moves that improve the position by more than 0.5 pawns are **best**; the rest are **good**."""

# ------------------------------------------------------------------
# Labels
# ------------------------------------------------------------------

CLASSIFICATION_BLUNDER = "blunder"
CLASSIFICATION_MISTAKE = "mistake"
CLASSIFICATION_INACCURACY = "inaccuracy"
CLASSIFICATION_GOOD = "good"
CLASSIFICATION_BEST = "best"

ALL_CLASSIFICATIONS = (
    CLASSIFICATION_BLUNDER,
    CLASSIFICATION_MISTAKE,
    CLASSIFICATION_INACCURACY,
    CLASSIFICATION_GOOD,
    CLASSIFICATION_BEST,
)


# ------------------------------------------------------------------
# Helper
# ------------------------------------------------------------------

def classify_move_by_eval_diff(eval_diff: float) -> str:
    """Classify a move based on how much the evaluation changed.

    Parameters
    ----------
    eval_diff:
        ``eval_before − eval_after`` from the **moving player's** perspective.
        A positive value means the position worsened; a negative value means
        it improved.

    Returns
    -------
    str
        One of the ``CLASSIFICATION_*`` constants defined in this module.
    """
    if eval_diff > BLUNDER_THRESHOLD:
        return CLASSIFICATION_BLUNDER
    if eval_diff > MISTAKE_THRESHOLD:
        return CLASSIFICATION_MISTAKE
    if eval_diff > INACCURACY_THRESHOLD:
        return CLASSIFICATION_INACCURACY
    if eval_diff > GOOD_THRESHOLD:
        return CLASSIFICATION_GOOD
    return CLASSIFICATION_BEST
