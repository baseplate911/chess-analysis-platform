"""Pydantic v2 schemas for request/response validation in the Chess Analysis Platform."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr


# ---------------------------------------------------------------------------
# User schemas
# ---------------------------------------------------------------------------

class UserCreate(BaseModel):
    """Schema for creating a new user account."""

    email: EmailStr
    username: str
    password: str


class UserLogin(BaseModel):
    """Schema for user login credentials."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for returning user data (excludes sensitive fields)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str
    created_at: datetime


class Token(BaseModel):
    """Schema for the JWT access token response."""

    access_token: str
    token_type: str = "bearer"


# ---------------------------------------------------------------------------
# Game schemas
# ---------------------------------------------------------------------------

class GameCreate(BaseModel):
    """Schema for submitting a new game for storage."""

    pgn: str
    result: Optional[str] = None
    analysis_json: Optional[str] = None


class GameResponse(BaseModel):
    """Schema for returning a stored game record."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    pgn: str
    result: Optional[str]
    analysis_json: Optional[str]
    created_at: datetime

    # Computed stats derived from analysis_json for dashboard / history display
    move_count: Optional[int] = None
    accuracy: Optional[float] = None
    blunders: Optional[int] = None

    @classmethod
    def model_validate(cls, obj, **kwargs):
        """Populate computed stats from analysis_json when constructing from an ORM model."""
        instance = super().model_validate(obj, **kwargs)
        if instance.analysis_json:
            try:
                data = json.loads(instance.analysis_json)
                moves = data.get("moves", [])
                instance.move_count = len(moves)
                instance.blunders = sum(
                    1 for m in moves if m.get("classification") == "blunder"
                )
                summary = data.get("summary", {})
                if summary.get("accuracy") is not None:
                    instance.accuracy = float(summary["accuracy"])
            except Exception:
                pass
        return instance


class MoveAnalysis(BaseModel):
    """Schema for an individual move analysis result."""

    move_number: int
    move: str
    classification: str
    eval_before: float
    eval_after: float
    eval_diff: float
    eval: Optional[float] = None
    best_move: Optional[str] = None


class GameAnalysis(BaseModel):
    """Schema for the full analysis result of a game."""

    pgn: str
    result: str
    moves: List[MoveAnalysis]
    win_probabilities: List[Dict[str, float]]
    summary: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Player profile schemas
# ---------------------------------------------------------------------------

class PlayerProfileResponse(BaseModel):
    """Schema for returning a player's profile and statistics."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    style: str
    accuracy: float
    total_games: int
    stats_json: Optional[str]
    updated_at: datetime
