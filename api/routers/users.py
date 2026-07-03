"""
User profile API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from api.dependencies import (
    get_current_user,
    get_profile_service,
    get_onboarding_service,
    get_user_repo,
)
from recommendation.user.schemas import UserProfile, UserPreferences

router = APIRouter(prefix="/users", tags=["Users"])


# ── Request schemas ────────────────────────────────────────────────

class UpdateProfileRequest(BaseModel):
    username: str | None = None
    preferences: UserPreferences | None = None


class OnboardingRequest(BaseModel):
    selected_tmdb_ids: list[int] = Field(..., min_length=10)


# ── Endpoints ──────────────────────────────────────────────────────

@router.get("/me")
def get_me(user: UserProfile = Depends(get_current_user)):
    """Get the authenticated user's profile."""
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "onboarded": user.onboarded,
        "preferences": user.preferences.model_dump(),
        "watch_history": user.watch_history[:20],
        "watchlist": user.watchlist,
        "ratings": user.ratings,
        "ratings_count": len(user.ratings),
        "liked": user.liked,
        "liked_count": len(user.liked),
        "disliked": user.disliked,
    }


@router.put("/me")
def update_me(
    req: UpdateProfileRequest,
    user: UserProfile = Depends(get_current_user),
):
    """Update the authenticated user's profile."""
    repo = get_user_repo()

    if req.username is not None:
        user.username = req.username
    if req.preferences is not None:
        user.preferences = req.preferences

    updated = repo.update(user)
    return {
        "message": "Profile updated",
        "username": updated.username,
        "preferences": updated.preferences.model_dump(),
    }


@router.post("/onboarding")
def complete_onboarding(
    req: OnboardingRequest,
    user: UserProfile = Depends(get_current_user),
):
    """Submit 10+ movie selections to complete onboarding."""
    svc = get_onboarding_service()

    try:
        updated = svc.complete_onboarding(user.id, req.selected_tmdb_ids)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )

    return {
        "message": "Onboarding complete",
        "onboarded": updated.onboarded,
        "preferences": updated.preferences.model_dump(),
        "liked_count": len(updated.liked),
    }


@router.get("/onboarding/movies")
def get_onboarding_movies(
    count: int = Query(50, ge=10, le=100),
):
    """Get popular + diverse movies for the onboarding selection UI."""
    svc = get_onboarding_service()
    return {"movies": svc.get_onboarding_movies(count=count)}
