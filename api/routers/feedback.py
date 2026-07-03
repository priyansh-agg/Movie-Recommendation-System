"""
Feedback API endpoints — rate, like, dislike, watchlist, watched.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.dependencies import get_current_user, get_interaction_service
from recommendation.user.schemas import UserProfile

router = APIRouter(prefix="/feedback", tags=["Feedback"])


# ── Request schemas ────────────────────────────────────────────────

class RateRequest(BaseModel):
    tmdb_id: int
    rating: float = Field(ge=0.5, le=5.0)


class MovieRequest(BaseModel):
    tmdb_id: int


class WatchlistRequest(BaseModel):
    tmdb_id: int
    action: str = Field(pattern=r"^(add|remove)$")


# ── Endpoints ──────────────────────────────────────────────────────

@router.post("/rate")
def rate_movie(
    req: RateRequest,
    user: UserProfile = Depends(get_current_user),
):
    """Rate a movie (0.5–5.0)."""
    svc = get_interaction_service()
    try:
        svc.rate_movie(user.id, req.tmdb_id, req.rating)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    return {"message": f"Rated movie {req.tmdb_id} with {req.rating}"}


@router.post("/like")
def like_movie(
    req: MovieRequest,
    user: UserProfile = Depends(get_current_user),
):
    """Like a movie."""
    svc = get_interaction_service()
    svc.like_movie(user.id, req.tmdb_id)
    return {"message": f"Liked movie {req.tmdb_id}"}


@router.post("/dislike")
def dislike_movie(
    req: MovieRequest,
    user: UserProfile = Depends(get_current_user),
):
    """Dislike a movie."""
    svc = get_interaction_service()
    svc.dislike_movie(user.id, req.tmdb_id)
    return {"message": f"Disliked movie {req.tmdb_id}"}


@router.post("/watchlist")
def update_watchlist(
    req: WatchlistRequest,
    user: UserProfile = Depends(get_current_user),
):
    """Add or remove a movie from the watchlist."""
    svc = get_interaction_service()
    if req.action == "add":
        svc.add_to_watchlist(user.id, req.tmdb_id)
        return {"message": f"Added movie {req.tmdb_id} to watchlist"}
    else:
        svc.remove_from_watchlist(user.id, req.tmdb_id)
        return {"message": f"Removed movie {req.tmdb_id} from watchlist"}


@router.post("/watched")
def mark_watched(
    req: MovieRequest,
    user: UserProfile = Depends(get_current_user),
):
    """Mark a movie as watched."""
    svc = get_interaction_service()
    svc.mark_watched(user.id, req.tmdb_id)
    return {"message": f"Marked movie {req.tmdb_id} as watched"}
