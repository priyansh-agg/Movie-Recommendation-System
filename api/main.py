"""
FastAPI application entry point.

Run with:
    uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from dotenv import load_dotenv

load_dotenv()

from api.auth.router import router as auth_router
from api.routers.recommendations import router as rec_router
from api.routers.search import router as search_router
from api.routers.users import router as users_router
from api.routers.feedback import router as feedback_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Warm up ML models at startup so the first request isn't slow."""
    print("[startup] Loading recommendation models...")
    from recommendation.content_based.loader import (
        similarity, similarity_sparse, SIMILARITY_MODE, movie_titles,
    )
    from recommendation.collaborative.recommender import model

    if SIMILARITY_MODE == "sparse":
        sim_info = f"Sparse similarity ({len(similarity_sparse):,} movies, top-50)"
    else:
        sim_info = f"Dense similarity matrix: {similarity.shape}"

    print(
        f"[startup] Models ready. "
        f"{sim_info}, "
        f"Movies: {len(movie_titles):,}, "
        f"SVD model loaded."
    )
    yield
    print("[shutdown] Cleaning up...")


app = FastAPI(
    title="Movie Recommendation API",
    description=(
        "Netflix-style movie recommendation system with hybrid engine, "
        "user intelligence layer, and evaluation framework."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ─────────────────────────────────────────────────────────
API_PREFIX = "/api/v1"

app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(rec_router, prefix=API_PREFIX)
app.include_router(search_router, prefix=API_PREFIX)
app.include_router(users_router, prefix=API_PREFIX)
app.include_router(feedback_router, prefix=API_PREFIX)


# ── Error handlers ──────────────────────────────────────────────────


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400, content={"detail": str(exc)}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# ── Root endpoints ──────────────────────────────────────────────────


@app.get("/")
def root():
    return {
        "name": "Movie Recommendation API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "auth": f"{API_PREFIX}/auth",
            "recommendations": f"{API_PREFIX}/recommendations",
            "search": f"{API_PREFIX}/search",
            "users": f"{API_PREFIX}/users",
            "feedback": f"{API_PREFIX}/feedback",
        },
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
