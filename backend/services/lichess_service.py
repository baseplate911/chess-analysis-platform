"""Lichess API integration service for fetching live games."""

import json
import os
from typing import AsyncGenerator, Optional

import httpx

LICHESS_BASE = "https://lichess.org/api"
LICHESS_TOKEN = os.getenv("LICHESS_API_TOKEN", "")


class LichessService:
    """Provides access to public Lichess API endpoints for live game data."""

    async def get_current_game(self, username: str) -> Optional[dict]:
        """Fetch the ongoing game for a Lichess user.

        Calls the public endpoint GET /api/user/{username}/current-game and
        returns the first NDJSON line as a dict (the gameFull object).
        Returns None if the user has no ongoing game.
        """
        url = f"{LICHESS_BASE}/user/{username}/current-game"
        print(f"🔵 [LichessService] Fetching current game from: {url}")
        
        headers = {"Accept": "application/x-ndjson"}
        if LICHESS_TOKEN:
            headers["Authorization"] = f"Bearer {LICHESS_TOKEN}"
            print(f"✅ [LichessService] Using API token for authentication")
        else:
            print(f"⚠️ [LichessService] No API token - using public endpoint")
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.get(url, headers=headers)
                print(f"🔵 [LichessService] Response status: {response.status_code}")
                if response.status_code == 404:
                    print(f"🔴 [LichessService] User not found or no ongoing game")
                    return None
                response.raise_for_status()
                # The response may be empty or a single NDJSON line
                text = response.text.strip()
                print(f"🔵 [LichessService] Response text length: {len(text)}")
                if not text:
                    print(f"🔴 [LichessService] Empty response")
                    return None
                first_line = text.splitlines()[0].strip()
                if not first_line:
                    print(f"🔴 [LichessService] First line empty")
                    return None
                game_data = json.loads(first_line)
                print(f"✅ [LichessService] Successfully parsed game data")
                return game_data
            except httpx.HTTPStatusError as e:
                print(f"🔴 [LichessService] HTTP error: {e.response.status_code}")
                return None
            except json.JSONDecodeError as e:
                print(f"🔴 [LichessService] JSON decode error: {str(e)}")
                return None
            except Exception as e:
                print(f"🔴 [LichessService] Unexpected error: {type(e).__name__}: {str(e)}")
                import traceback
                traceback.print_exc()
                return None

    async def stream_game_moves(self, game_id: str) -> AsyncGenerator[dict, None]:
        """Stream move events for an ongoing game.

        Yields parsed NDJSON lines from GET /api/board/game/stream/{game_id}.
        Each yielded dict has a ``type`` field: ``"gameFull"`` (initial state)
        or ``"gameState"`` (each subsequent move update).
        
        REQUIRES: LICHESS_API_TOKEN environment variable set!
        """
        url = f"{LICHESS_BASE}/board/game/stream/{game_id}"
        print(f"🔵 [LichessService] Starting stream from: {url}")
        
        if not LICHESS_TOKEN:
            print(f"🔴 [LichessService] ERROR: No API token! Set LICHESS_API_TOKEN in .env")
            raise Exception("LICHESS_API_TOKEN not set. Cannot stream game moves without authentication.")
        
        print(f"✅ [LichessService] Using API token for stream")
        headers = {
            "Accept": "application/x-ndjson",
            "Authorization": f"Bearer {LICHESS_TOKEN}"
        }
        
        async with httpx.AsyncClient(timeout=None) as client:
            try:
                async with client.stream(
                    "GET",
                    url,
                    headers=headers,
                ) as response:
                    print(f"🔵 [LichessService] Stream response status: {response.status_code}")
                    response.raise_for_status()
                    line_count = 0
                    async for raw_line in response.aiter_lines():
                        line = raw_line.strip()
                        if not line:
                            continue
                        try:
                            line_count += 1
                            data = json.loads(line)
                            print(f"🔵 [LichessService] Streamed event #{line_count}: type={data.get('type')}")
                            yield data
                        except json.JSONDecodeError as e:
                            print(f"⚠️ [LichessService] Skipped invalid JSON line: {str(e)}")
                            continue
                    print(f"✅ [LichessService] Stream ended. Total events: {line_count}")
            except httpx.HTTPStatusError as e:
                print(f"🔴 [LichessService] HTTP error during stream: {e.response.status_code}")
                if e.response.status_code == 401:
                    print(f"🔴 [LichessService] 401 Unauthorized - Invalid or expired API token")
                raise
            except Exception as e:
                print(f"🔴 [LichessService] Error during stream: {type(e).__name__}: {str(e)}")
                import traceback
                traceback.print_exc()
                raise