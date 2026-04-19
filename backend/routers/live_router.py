"""WebSocket router for live Lichess game streaming with move prediction."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

import chess

from services.chess_service import ChessService
from services.lichess_service import LichessService
from services.ml_service import MLService

router = APIRouter(prefix="/live", tags=["Live"])

_chess_service = ChessService()
_ml_service = MLService()
_lichess_service = LichessService()

_GAME_OVER_STATUSES = {"mate", "resign", "draw", "stalemate", "timeout", "outoftime"}


def _compute_summary(moves_analysis: list) -> dict:
    """Compute game summary statistics from a list of move analysis dicts."""
    blunders = sum(1 for m in moves_analysis if m.get("classification") == "Blunder")
    mistakes = sum(1 for m in moves_analysis if m.get("classification") == "Mistake")
    inaccuracies = sum(1 for m in moves_analysis if m.get("classification") == "Inaccuracy")
    good = sum(1 for m in moves_analysis if m.get("classification") == "Good")
    great = sum(1 for m in moves_analysis if m.get("classification") == "Great")
    brilliant = sum(1 for m in moves_analysis if m.get("classification") == "Brilliant")
    total = len(moves_analysis)
    accuracy = round((good + great + brilliant) / total * 100, 1) if total else 0.0
    return {
        "blunders": blunders,
        "mistakes": mistakes,
        "inaccuracies": inaccuracies,
        "good": good,
        "great": great,
        "brilliant": brilliant,
        "accuracy": accuracy,
    }


def _parse_moves(moves_str: str, moves_analysis: list) -> list:
    """Reconstruct board from UCI move string and analyse each move.

    Returns an updated moves_analysis list with entries for all moves.
    """
    board = chess.Board()
    uci_moves = moves_str.split() if moves_str else []
    result = []
    eval_before = _chess_service._evaluate_position(board)

    for idx, uci in enumerate(uci_moves):
        try:
            move = chess.Move.from_uci(uci)
        except ValueError:
            print(f"⚠️ Invalid UCI move: {uci}")
            continue

        if move not in board.legal_moves:
            print(f"⚠️ Illegal move: {uci}")
            continue

        move_san = board.san(move)
        is_white = board.turn == chess.WHITE
        move_number = idx + 1

        board.push(move)
        eval_after = _chess_service._evaluate_position(board)
        perspective_before = eval_before if is_white else -eval_before
        perspective_after = eval_after if is_white else -eval_after

        classification = _chess_service.classify_move(perspective_before, perspective_after)
        features = _chess_service.extract_features(board)
        probs = _ml_service.predict_win_probability([eval_after] + features[1:])
        classification = _chess_service.classify_move(perspective_before, perspective_after)
        print(f"Move {move_number}: {move_san} | Classification: '{classification}'")
        features = _chess_service.extract_features(board)

        result.append({
            "move_number": move_number,
            "move": move_san,
            "fen": board.fen(),
            "classification": classification,
            "eval": round(perspective_after, 3),
            "white_win": round(probs[0] * 100, 1),
            "draw": round(probs[1] * 100, 1),
            "black_win": round(probs[2] * 100, 1),
        })

        eval_before = eval_after

    return result


@router.websocket("/ws/{username}")
async def live_game_ws(websocket: WebSocket, username: str):
    """Stream live move predictions for a user's ongoing Lichess game."""
    await websocket.accept()

    try:
        print(f"🔵 Fetching current game for user: {username}")
        game_data = await _lichess_service.get_current_game(username)
    except Exception as e:
        print(f"🔴 Error fetching game: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        game_data = None

    if not game_data:
        print(f"🔴 No ongoing game found for {username}")
        await websocket.send_json({
            "type": "error",
            "message": (
                f"No ongoing game found for {username}. "
                "Please start a game on Lichess first."
            ),
        })
        await websocket.close()
        return

    game_id = game_data.get("id", "")
    white_player = (
        game_data.get("players", {}).get("white", {}).get("user", {}).get("name", "White")
        or game_data.get("white", {}).get("name", "White")
    )
    black_player = (
        game_data.get("players", {}).get("black", {}).get("user", {}).get("name", "Black")
        or game_data.get("black", {}).get("name", "Black")
    )
    clock = game_data.get("clock", {})
    time_control = (
        f"{clock.get('initial', 0) // 60}+{clock.get('increment', 0)}"
        if clock
        else game_data.get("speed", "unknown")
    )

    print(f"✅ Found game: {game_id}")
    print(f"✅ Players: {white_player} vs {black_player}")
    print(f"✅ Time control: {time_control}")

    await websocket.send_json({
        "type": "connected",
        "game_id": game_id,
        "white": white_player,
        "black": black_player,
        "time_control": time_control,
    })

    moves_analysis: list = []

    try:
        print(f"🔵 Starting to stream moves for game {game_id}")
        async for event in _lichess_service.stream_game_moves(game_id):
            print(f"📨 Received event from Lichess")
            event_type = event.get("type")
            print(f"📨 Event type: {event_type}")

            # gameFull is emitted once at the start; analyse its current state
            if event_type == "gameFull":
                state = event.get("state", {})
                moves_str = state.get("moves", "")
                status = state.get("status", "started")
                print(f"🎮 gameFull event received")
                print(f"🎮 Moves: {moves_str[:100] if moves_str else 'No moves yet'}")
                print(f"🎮 Status: {status}")
            elif event_type == "gameState":
                moves_str = event.get("moves", "")
                status = event.get("status", "started")
                print(f"♟️ gameState event received")
                print(f"♟️ Moves: {moves_str[:100] if moves_str else 'No moves yet'}")
                print(f"♟️ Status: {status}")
            else:
                print(f"⚠️ Unknown event type: {event_type}, skipping")
                continue

            try:
                # Rebuild full analysis for all moves so far
                print(f"🔵 Parsing moves...")
                moves_analysis = _parse_moves(moves_str, moves_analysis)
                print(f"✅ Successfully parsed {len(moves_analysis)} moves")
            except Exception as parse_error:
                print(f"🔴 ERROR in _parse_moves: {type(parse_error).__name__}: {str(parse_error)}")
                import traceback
                traceback.print_exc()
                await websocket.send_json({
                    "type": "error",
                    "message": f"Error parsing moves: {str(parse_error)}",
                })
                break

            if moves_analysis:
                last = moves_analysis[-1]
                try:
                    print(f"🔵 Sending move update: {last['move']}")
                    await websocket.send_json({
                        "type": "move",
                        "move_number": last["move_number"],
                        "move": last["move"],
                        "fen": last["fen"],
                        "classification": last["classification"],
                        "eval": last["eval"],
                        "white_win": last["white_win"],
                        "draw": last["draw"],
                        "black_win": last["black_win"],
                    })
                    print(f"✅ Successfully sent move {last['move_number']}: {last['move']}")
                except Exception as send_error:
                    print(f"🔴 ERROR sending move: {type(send_error).__name__}: {str(send_error)}")
                    import traceback
                    traceback.print_exc()
                    break

            if status in _GAME_OVER_STATUSES:
                print(f"🏁 Game over! Status: {status}")
                winner = event.get("winner") or (
                    state.get("winner") if event_type == "gameFull" else None
                )
                summary = _compute_summary(moves_analysis)
                try:
                    print(f"🔵 Sending game_over message")
                    await websocket.send_json({
                        "type": "game_over",
                        "status": status,
                        "winner": winner,
                        "moves": moves_analysis,
                        "summary": summary,
                    })
                    print(f"✅ Successfully sent game_over message")
                except Exception as send_error:
                    print(f"🔴 ERROR sending game_over: {type(send_error).__name__}: {str(send_error)}")
                    import traceback
                    traceback.print_exc()
                break

    except WebSocketDisconnect:
        print(f"ℹ️ WebSocket disconnected by client")
        pass
    except Exception as e:
        print(f"🔴 BACKEND STREAMING ERROR: {type(e).__name__}")
        print(f"🔴 ERROR MESSAGE: {str(e)}")
        import traceback
        print(f"🔴 FULL TRACEBACK:")
        traceback.print_exc()
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Streaming error: {str(e)}",
            })
        except Exception as final_error:
            print(f"🔴 Could not send error to client: {str(final_error)}")