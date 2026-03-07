"""Lichess API integration service for fetching live games."""

import json
from typing import AsyncGenerator, Optional

import httpx

LICHESS_BASE = "https://lichess.org/api"


class LichessService:
    """Provides access to public Lichess API endpoints for live game data."""

    async def get_current_game(self, username: str) -> Optional[dict]:
        """Fetch the ongoing game for a Lichess user.

        Calls the public endpoint GET /api/user/{username}/current-game and
        returns the first NDJSON line as a dict (the gameFull object).
        Returns None if the user has no ongoing game.
        """
        url = f"{LICHESS_BASE}/user/{username}/current-game"
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.get(
                    url,
                    headers={"Accept": "application/x-ndjson"},
                )
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                # The response may be empty or a single NDJSON line
                text = response.text.strip()
                if not text:
                    return None
                first_line = text.splitlines()[0].strip()
                if not first_line:
                    return None
                return json.loads(first_line)
            except (httpx.HTTPStatusError, json.JSONDecodeError):
                return None

    async def stream_game_moves(self, game_id: str) -> AsyncGenerator[dict, None]:
        """Stream move events for an ongoing game.

        Yields parsed NDJSON lines from GET /api/board/game/stream/{game_id}.
        Each yielded dict has a ``type`` field: ``"gameFull"`` (initial state)
        or ``"gameState"`` (each subsequent move update).
        """
        url = f"{LICHESS_BASE}/board/game/stream/{game_id}"
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "GET",
                url,
                headers={"Accept": "application/x-ndjson"},
            ) as response:
                response.raise_for_status()
                async for raw_line in response.aiter_lines():
                    line = raw_line.strip()
                    if not line:
                        continue
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        continue
