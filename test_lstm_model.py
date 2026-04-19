"""Full game analysis using LSTM model."""

import numpy as np
from tensorflow.keras.models import load_model
import pickle
import chess
import chess.pgn
from io import StringIO
import json

# Load model and supporting files
model = load_model('ml_model/win_probability/final_lstm_model.keras')

with open('ml_model/win_probability/scaler.pkl', 'rb') as f:
    scaler = pickle.load(f)

with open('ml_model/win_probability/move_to_idx.pkl', 'rb') as f:
    move_to_idx = pickle.load(f)

def get_material_count(board):
    """Calculate material difference (White - Black)."""
    piece_values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
    }
    
    white_material = sum(
        piece_values.get(board.piece_type_at(sq), 0) 
        for sq in chess.SQUARES 
        if board.color_at(sq) == chess.WHITE
    )
    
    black_material = sum(
        piece_values.get(board.piece_type_at(sq), 0) 
        for sq in chess.SQUARES 
        if board.color_at(sq) == chess.BLACK
    )
    
    return white_material - black_material

def analyze_game(pgn_string):
    """Analyze a full game move by move."""
    
    game = chess.pgn.read_game(StringIO(pgn_string))
    
    if game is None:
        print("Invalid PGN!")
        return
    
    # Extract game info
    white_player = game.headers.get("White", "Unknown")
    black_player = game.headers.get("Black", "Unknown")
    white_elo = int(game.headers.get("WhiteElo", 1600))
    black_elo = int(game.headers.get("BlackElo", 1600))
    result = game.headers.get("Result", "*")
    
    print("="*80)
    print(f"FULL GAME ANALYSIS")
    print("="*80)
    print(f"\n{white_player} ({white_elo}) vs {black_player} ({black_elo})")
    print(f"Result: {result}\n")
    
    board = game.board()
    moves_list = []
    win_probs = []
    
    move_num = 1
    print(f"{'Move':<6} {'Action':<15} {'White %':<12} {'Draw %':<12} {'Black %':<12}")
    print("-"*80)
    
    for move in game.mainline_moves():
        san_move = board.san(move)
        moves_list.append(san_move)
        
        # Get material
        material = get_material_count(board)
        
        # Create LSTM input
        move_indices = [move_to_idx.get(m, 0) for m in moves_list]
        
        # Pad to 100
        move_seq = move_indices + [0] * (100 - len(move_indices))
        move_seq = move_seq[:100]
        
        X_moves = np.array([move_seq], dtype='int32')
        X_numeric = np.array([[white_elo, black_elo, material]], dtype='float32')
        X_numeric_scaled = scaler.transform(X_numeric)
        
        # Predict
        prediction = model.predict([X_moves, X_numeric_scaled], verbose=0)
        white_prob = prediction[0][0]
        draw_prob = prediction[0][2]
        black_prob = prediction[0][1]
        
        win_probs.append({
            'move': move_num,
            'san': san_move,
            'white': white_prob,
            'draw': draw_prob,
            'black': black_prob,
            'material': material
        })
        
        # Print move analysis
        move_type = "White" if move_num % 2 == 1 else "Black"
        print(f"{move_num:<6} {san_move:<15} {white_prob*100:>10.2f}% {draw_prob*100:>10.2f}% {black_prob*100:>10.2f}%")
        
        board.push(move)
        move_num += 1
    
    print("-"*80)
    
    # Final analysis
    print(f"\n\nFINAL ANALYSIS:")
    print("="*80)
    
    final_probs = win_probs[-1]
    print(f"\nFinal Position Probabilities:")
    print(f"  White wins: {final_probs['white']*100:.2f}%")
    print(f"  Draw:       {final_probs['draw']*100:.2f}%")
    print(f"  Black wins: {final_probs['black']*100:.2f}%")
    
    print(f"\nActual Result: {result}")
    
    # Turning points
    print(f"\n\nTURNING POINTS:")
    print("-"*80)
    
    max_white = max(win_probs, key=lambda x: x['white'])
    max_black = max(win_probs, key=lambda x: x['black'])
    
    print(f"\nBest for White: Move {max_white['move']} ({max_white['san']})")
    print(f"  White: {max_white['white']*100:.2f}% | Draw: {max_white['draw']*100:.2f}% | Black: {max_white['black']*100:.2f}%")
    
    print(f"\nBest for Black: Move {max_black['move']} ({max_black['san']})")
    print(f"  White: {max_black['white']*100:.2f}% | Draw: {max_black['draw']*100:.2f}% | Black: {max_black['black']*100:.2f}%")
    
    # Momentum shifts
    print(f"\n\nMOMENTUM SHIFTS (by 10% or more):")
    print("-"*80)
    
    for i in range(1, len(win_probs)):
        prev = win_probs[i-1]
        curr = win_probs[i]
        
        white_shift = curr['white'] - prev['white']
        black_shift = curr['black'] - prev['black']
        
        if abs(white_shift) > 0.1 or abs(black_shift) > 0.1:
            move_type = "White" if curr['move'] % 2 == 1 else "Black"
            print(f"\nMove {curr['move']} ({curr['san']}) - {move_type} to move")
            if white_shift > 0.1:
                print(f"  ↑ White gained {white_shift*100:.2f}%")
            elif white_shift < -0.1:
                print(f"  ↓ White lost {abs(white_shift)*100:.2f}%")
            if black_shift > 0.1:
                print(f"  ↑ Black gained {black_shift*100:.2f}%")
            elif black_shift < -0.1:
                print(f"  ↓ Black lost {abs(black_shift)*100:.2f}%")
    
    print("\n" + "="*80)
    
    return win_probs


# Example: Fool's Mate
fool_mate = """
[Event "Fool's Mate"]
[Site "Example"]
[White "White Player"]
[Black "Black Player"]
[WhiteElo "1600"]
[BlackElo "1600"]
[Result "0-1"]

1. f3 e5 2. g4 Qh4#
"""

print("\n\nANALYZING FOOL'S MATE:\n")
analyze_game(fool_mate)

# ============================================================================
# EXAMPLE 2: A longer game
# ============================================================================

longer_game = """
[Event "Sample Game"]
[White "Akash"]
[Black "Opponent"]
[WhiteElo "2000"]
[BlackElo "1950"]
[Result "1-0"]

1. e4 c5 2. Nf3 d6 3. d4 cxd4 4. Nxd4 Nf6 5. Nc3 a6 6. Be3 e5 7. Nb3 Be6 
8. f3 Be7 9. Qd2 O-O 10. O-O-O Nbd7 11. g4 b5 12. g5 b4 13. Ne2 Ne8 14. f4 a5 
15. f5 Bxf5 16. Qxf5 exf4 17. Bf4 Nxg5 18. Qg4 Ne6 19. Bxe6 fxe6 20. Qxe6+ Kh8 
21. Kb1 Nf6 22. Qe7 Qc7 23. Qxc7 Nxc7 24. Rhe1 a4 25. Nc1 a3 26. b3 Rab8 
27. Nd3 Rfc8 28. Nxf4 Rc1+ 29. Ka2 Rxa1 30. Nxd6 Rb1 31. Nxb7 Rxb3 32. Nd8 Rbb1 
33. Ne6 R1b2 34. Nf4 Rf2 35. Nd3 Rfxf4 36. Nxf4 Rxd1 37. Nxd1
"""

print("\n\n\nANALYZING LONGER GAME:\n")
analyze_game(longer_game)