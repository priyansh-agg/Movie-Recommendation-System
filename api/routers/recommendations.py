"""
Recommendation API endpoints.
"""

from fastapi import APIRouter, Depends, Query

from api.dependencies import (
    get_current_user,
    get_optional_user,
    get_recommendation_service,
    get_homepage_orchestrator,
    get_profile_service,
)
from recommendation.user.schemas import UserProfile

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("/similar")
def get_similar(
    movies: list[str] = Query(
        ..., description="Movie titles to find similar movies for"
    ),
    top_n: int = Query(10, ge=1, le=50),
):
    """Content-based: 'Movies like X'."""
    svc = get_recommendation_service()
    recs = svc.recommend_similar(movies, top_n=top_n)
    return {"recommendations": [r.model_dump() for r in recs]}


@router.get("/for-user")
def get_for_user(
    top_n: int = Query(10, ge=1, le=50),
    user: UserProfile = Depends(get_current_user),
):
    """Hybrid personalised recommendations for the authenticated user."""
    svc = get_recommendation_service()
    ps = get_profile_service()

    liked_titles = ps.get_liked_movie_titles(user.id)

    recs = svc.recommend_for_user(
        user_id=user.movielens_user_id,
        liked_movies=liked_titles or None,
        top_n=top_n,
    )
    return {"recommendations": [r.model_dump() for r in recs]}


@router.get("/homepage")
def get_homepage(
    user: UserProfile | None = Depends(get_optional_user),
):
    """Full Netflix-style homepage (anonymous or personalised)."""
    orch = get_homepage_orchestrator()
    ps = get_profile_service()

    if user is not None:
        liked_titles = ps.get_liked_movie_titles(user.id)
        sections = orch.get_homepage(
            user_id=user.movielens_user_id,
            liked_movies=liked_titles or None,
            user_profile=user,
        )
    else:
        sections = orch.get_homepage()

    return {
        "sections": [
            {
                "section_id": s.section_id,
                "title": s.title,
                "section_type": s.section_type,
                "movies": [m.model_dump() for m in s.movies],
            }
            for s in sections
        ]
    }
