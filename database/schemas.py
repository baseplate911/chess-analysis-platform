"""Pydantic v2 schemas for request/response validation in the Chess Analysis Platform."""

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


class MoveAnalysis(BaseModel):
    """Schema for an individual move analysis result."""

    move_number: int
    move: str
    classification: str
    eval_before: float
    eval_after: float
    eval_diff: float
    best_move: Optional[str] = None


class GameAnalysis(BaseModel):
    """Schema for the full analysis result of a game."""

    pgn: str
    result: str
    moves: List[MoveAnalysis]
    win_probabilities: List[Dict[str, float]]


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
