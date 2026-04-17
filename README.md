# ♟ Chess Analysis Platform

An **AI-powered chess game analysis platform** built as a final year computer science project. It combines a React.js frontend, a FastAPI backend, and three machine-learning models to give players deep insight into their games.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🧠 **AI Move Classification** | Every move is labelled Blunder / Mistake / Inaccuracy / Good / Best |
| 📈 **Win Probability Graph** | Live line chart showing win % after each half-move |
| ♟ **Interactive Board** | Navigate through every move with Prev/Next buttons |
| 📊 **Evaluation Bar** | Visual centipawn evaluation beside the board |
| 🎯 **Best Move Suggestion** | Stockfish (or heuristic) best-move hints |
| 👤 **Player Behaviour Profile** | Classifies your style: Aggressive / Defensive / Tactical / Positional |
| 📂 **Game History** | All analysed games saved and browsable |
| 🔐 **JWT Authentication** | Secure register / login with bcrypt passwords |
| 📱 **Responsive Design** | Works on desktop and mobile |

---

## 🏗 Project Structure

```
chess-analysis-platform/
├── frontend/                  # React.js + Vite + Tailwind CSS
│   ├── src/
│   │   ├── api/               # Axios API client
│   │   ├── components/        # Reusable UI components
│   │   ├── context/           # Auth context (JWT)
│   │   └── pages/             # Route pages
│   ├── Dockerfile
│   └── package.json
│
├── backend/                   # FastAPI Python backend
│   ├── routers/               # auth, analysis, player endpoints
│   ├── services/              # chess_service, ml_service
│   ├── auth.py                # JWT + bcrypt helpers
│   ├── main.py                # App entry point
│   └── Dockerfile
│
├── database/                  # SQLAlchemy + Pydantic
│   ├── database.py            # SQLite engine + session
│   ├── models.py              # User, Game, PlayerProfile ORM models
│   └── schemas.py             # Pydantic v2 schemas
│
├── ml_model/                  # ML models (LSTM + tree-based classifiers)
│   ├── win_probability/       # Win probability predictor
│   ├── blunder_detector/      # Move quality classifier
│   ├── player_behaviour/      # Player style classifier
│   ├── data_processing/       # PGN parser + feature extractor
│   └── README.md              # How to train on real data
│
├── docker-compose.yml
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variable template
└── README.md                  # This file
```

---

## 🚀 Quick Start

### Option 1 — Docker (recommended)

```bash
# 1. Clone the repo
git clone https://github.com/baseplate911/chess-analysis-platform.git
cd chess-analysis-platform

# 2. Copy environment file
cp .env.example .env
# Edit .env and set a strong SECRET_KEY

# 3. Start everything
docker-compose up --build
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

### Option 2 — Manual Setup

#### Backend

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Copy and edit environment variables
cp .env.example .env

# Start the FastAPI server (from repo root)
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend
npm install
npm run dev          # Development server on http://localhost:5173
# or
npm run build && npm run preview   # Production build
```

---

## ⚙️ Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | *(required)* | JWT signing key — use a long random string in production |
| `STOCKFISH_PATH` | `/usr/local/bin/stockfish` | Path to Stockfish binary (optional) |
| `DATABASE_URL` | `sqlite:///./chess_analysis.db` | SQLAlchemy database URL |
| `FRONTEND_URL` | `http://localhost:3000` | Frontend URL (for CORS) |

### Installing Stockfish (optional but recommended)

```bash
# Ubuntu/Debian
sudo apt install stockfish

# macOS
brew install stockfish

# Windows — download from https://stockfishchess.org/download/
```

If Stockfish is not found, the backend gracefully falls back to heuristic evaluation using **python-chess**.

---

## 🌐 API Documentation

When the backend is running, interactive API docs are at:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Endpoints

#### Auth
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register` | Register new user, returns JWT |
| POST | `/api/auth/login` | Login, returns JWT |
| GET | `/api/auth/me` | Get current user info |

#### Analysis
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/analyze/game` | Analyse full PGN, returns moves + win probabilities |
| POST | `/api/analyze/position` | Analyse FEN position, returns eval + best move |
| GET | `/api/analyze/history` | Get user's past games |
| POST | `/api/analyze/save` | Save analysis to history |

#### Player
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/player/profile` | Get player behaviour profile |
| POST | `/api/player/classify` | Classify player style |

---

## 🤖 ML Models

Three ML models are included. The win-probability model is a fine-tuned LSTM, while the other two remain tree-based classifiers.

### Model 1: Win Probability Predictor
- **Architecture:** Fine-tuned LSTM (Embedding 64, LSTM 128 + numeric fusion)
- **Input:** Move sequence (max 100) + numeric features (`white_elo`, `black_elo`, `material`)
- **Output:** `{white_win, draw, black_win}` probabilities
- **Performance:** 90.43% test accuracy (171,332 games)

### Model 2: Blunder Detector
- **Architecture:** RandomForestClassifier
- **Input:** Board features + evaluation difference
- **Output:** `blunder / mistake / inaccuracy / good / best`

### Model 3: Player Behaviour Classifier
- **Architecture:** RandomForestClassifier
- **Input:** Aggregate game statistics
- **Output:** `Aggressive / Defensive / Tactical / Positional`

See [`ml_model/README.md`](ml_model/README.md) for full training instructions on real Lichess data.

### Training on Real Data

```bash
# Download Lichess open database (PGN files)
# https://database.lichess.org/

# Train each model
python ml_model/win_probability/train.py
python ml_model/blunder_detector/train.py
python ml_model/player_behaviour/train.py
```

---

## 🗄️ Database

SQLite is used by default — no external database server needed. The file `chess_analysis.db` is created automatically in the working directory on first run.

To switch to PostgreSQL, update `DATABASE_URL` in `.env`:
```
DATABASE_URL=postgresql://user:password@localhost:5432/chess_db
```

---

## 🖥️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18, Vite, Tailwind CSS, React Router v6 |
| **UI Libraries** | react-chessboard, chess.js, Recharts |
| **API Client** | Axios |
| **Backend** | Python 3.11, FastAPI, Uvicorn |
| **Auth** | JWT (python-jose), bcrypt (passlib) |
| **Database** | SQLite + SQLAlchemy 2, Pydantic v2 |
| **Chess Engine** | python-chess (+ optional Stockfish) |
| **ML** | scikit-learn, NumPy, joblib |
| **Deployment** | Docker, Docker Compose, Nginx |

---

## 🎯 User Flow

```
1. Visit / → Landing page
2. Register or Login → JWT stored in localStorage
3. Navigate to /analyze
4. Paste PGN or upload .pgn file
5. Click "Analyze" → backend processes game
6. Frontend displays:
   ├── Chess board with move navigation
   ├── Win probability chart (line graph)
   ├── Move list (colour-coded by quality)
   └── Best move suggestions
7. Save game to history
8. Visit /dashboard → personal stats + player profile
9. Visit /history → browse past games
```

---

## 📸 Screenshots

> *(Screenshots will be added after deployment)*

---

## 🔮 Future Improvements

- [ ] Real-time multiplayer analysis with WebSockets
- [ ] Opening book integration (ECO codes)
- [ ] Lichess / Chess.com account import
- [ ] Engine depth configuration
- [ ] Mobile app (React Native)
- [ ] ELO rating tracker over time
- [ ] Endgame tablebase integration
- [ ] Cloud deployment (AWS/GCP)

---

## 📄 License

MIT License

---

## 🙏 Acknowledgements

- [Lichess](https://lichess.org) for open game databases
- [Stockfish](https://stockfishchess.org) for the chess engine
- [python-chess](https://python-chess.readthedocs.io) for PGN/FEN utilities
- [react-chessboard](https://github.com/Clariity/react-chessboard) for the board UI
