# Deployment Guide

## Render Deployment (Recommended)

### Step 1 — Push model files
Place these files into `ml_model/blunder_detector/` on your server:
- `chess_xgboost_model.json`
- `label_map.json`
- `features.json`

### Step 2 — Connect to Render
1. Go to https://render.com
2. Click "New" → "Blueprint"
3. Connect your GitHub repo
4. Render will auto-detect `render.yaml`
5. Click Deploy!

### Step 3 — Environment Variables
Set these in Render dashboard:
- `SECRET_KEY` — auto-generated
- `STOCKFISH_PATH` — `/usr/games/stockfish` (already set)
- `CORS_ORIGINS` — your frontend URL

## Local Development

### Run with Docker
```bash
docker-compose up --build
```

### Run without Docker
```bash
# Backend
pip install -r requirements.txt
cd backend
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Stockfish

Stockfish is automatically installed inside the Docker container via `apt-get install stockfish`.

For local development without Docker:
- **Windows**: Download from https://stockfishchess.org/download/ and add to PATH
- **Mac**: `brew install stockfish`
- **Linux**: `sudo apt-get install stockfish`
