"""Entry point for the Chess Analysis Platform FastAPI application."""

import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure the repo root is on sys.path so that `database` package is importable
# when the server is launched from inside the backend/ directory.
_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from database.database import Base, engine
from routers import analysis_router, auth_router, player_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create all database tables on application startup."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Chess Analysis Platform API",
    description="Backend API for analysing chess games and player behaviour.",
    version="1.0.0",
    lifespan=lifespan,
)

# Support multiple origins: the production frontend URL plus the Vite dev server.
_frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
_allowed_origins = list({_frontend_url, "http://localhost:3000", "http://localhost:5173"})

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router, prefix="/api")
app.include_router(analysis_router.router, prefix="/api")
app.include_router(player_router.router, prefix="/api")


@app.get("/health", tags=["Health"])
def health_check():
    """Simple health-check endpoint."""
    return {"status": "ok"}
