"""Test router for unauthenticated testing of chess analysis."""

from fastapi import APIRouter
from pydantic import BaseModel

from services.chess_service import ChessService

router = APIRouter(prefix="/test", tags=["Test"])
chess_service = ChessService()


class PGNRequest(BaseModel):
    """Request body containing a PGN game string."""
    pgn: str


@router.post("/analyze-game")
def test_analyze_game(request: PGNRequest):
    """Test endpoint: analyse a game WITHOUT authentication."""
    try:
        result = chess_service.analyze_game(request.pgn)
        return result
    except Exception as exc:
        return {"error": str(exc)}