"""Entry point for the Chess Analysis Platform FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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
