"""Player router: profile retrieval and style classification endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth import get_current_user
from database.database import get_db
from database.models import PlayerProfile, User
from database.schemas import PlayerProfileResponse
from services.ml_service import MLService

router = APIRouter(prefix="/player", tags=["Player"])
ml_service = MLService()


@router.get("/profile", response_model=PlayerProfileResponse)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the current user's player profile, creating one if it does not exist."""
    profile = db.query(PlayerProfile).filter(PlayerProfile.user_id == current_user.id).first()
    if not profile:
        profile = PlayerProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.post("/classify", response_model=PlayerProfileResponse)
def classify_player(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Run style classification on the current user's game history and update their profile."""
    profile = db.query(PlayerProfile).filter(PlayerProfile.user_id == current_user.id).first()
    if not profile:
        profile = PlayerProfile(user_id=current_user.id)
        db.add(profile)
        db.flush()

    stats = {
        "total_games": profile.total_games,
        "accuracy": profile.accuracy,
    }
    style = ml_service.classify_player_style(stats)
    profile.style = style
    profile.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(profile)
    return profile
