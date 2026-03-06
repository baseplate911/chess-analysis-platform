"""Analysis router: game analysis, position analysis, and history endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import get_current_user
from database.database import get_db
from database.models import Game, User
from database.schemas import GameAnalysis, GameCreate, GameResponse
from services.chess_service import ChessService

router = APIRouter(prefix="/analyze", tags=["Analysis"])
chess_service = ChessService()


class PGNRequest(BaseModel):
    """Request body containing a PGN game string."""

    pgn: str


class FENRequest(BaseModel):
    """Request body containing a FEN position string."""

    fen: str


@router.post("/game", response_model=GameAnalysis)
def analyze_game(
    request: PGNRequest,
    current_user: User = Depends(get_current_user),
):
    """Parse and analyse every move in a PGN game string."""
    try:
        result = chess_service.analyze_game(request.pgn)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to analyse game: {exc}",
        )
    return result


@router.post("/position")
def analyze_position(
    request: FENRequest,
    current_user: User = Depends(get_current_user),
):
    """Evaluate a single board position given in FEN notation."""
    try:
        result = chess_service.analyze_position(request.fen)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to analyse position: {exc}",
        )
    return result


@router.get("/history", response_model=List[GameResponse])
def get_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return all previously analysed games for the current user."""
    return db.query(Game).filter(Game.user_id == current_user.id).all()


@router.post("/save", response_model=GameResponse, status_code=status.HTTP_201_CREATED)
def save_game(
    game_data: GameCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save a game (optionally with analysis JSON) to the user's history."""
    game = Game(
        user_id=current_user.id,
        pgn=game_data.pgn,
        result=game_data.result,
        analysis_json=game_data.analysis_json,
    )
    db.add(game)
    db.commit()
    db.refresh(game)
    return game
