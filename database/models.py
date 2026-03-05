"""SQLAlchemy ORM models for the Chess Analysis Platform."""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database.database import Base


def _utcnow() -> datetime:
    """Return the current UTC time as a timezone-aware datetime."""
    return datetime.now(timezone.utc)


class User(Base):
    """Represents a registered user of the platform."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    games = relationship("Game", back_populates="owner")
    profile = relationship("PlayerProfile", back_populates="owner", uselist=False)


class Game(Base):
    """Stores a chess game and its associated analysis data."""

    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pgn = Column(Text, nullable=False)
    result = Column(String, nullable=True)
    analysis_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    owner = relationship("User", back_populates="games")


class PlayerProfile(Base):
    """Stores the computed playing style and statistics for a user."""

    __tablename__ = "player_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    style = Column(String, default="unknown")
    accuracy = Column(Float, default=0.0)
    total_games = Column(Integer, default=0)
    stats_json = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    owner = relationship("User", back_populates="profile")
