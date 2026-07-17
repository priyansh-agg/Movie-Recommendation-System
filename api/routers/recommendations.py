"""
Recommendation API endpoints.
"""

import logging

from fastapi import APIRouter, Depends, Query

from api.dependencies import (
    get_current_user,
    get_optional_user,
    get_recommendation_service,
    get_homepage_orchestrator,
    get_profile_service,
    get_redis_cache,
)
from recommendation.user.schemas import UserProfile
from recommendation.db.redis_cache import TTL_HOMEPAGE, TTL_SIMILAR

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("/similar")
def get_similar(
    movies: list[str] = Query(
        ..., description="Movie titles to find similar movies for"
    ),
    top_n: int = Query(10, ge=1, le=50),
):
    """Content-based: 'Movies like X'."""
    cache = get_redis_cache()
    cache_key = cache.key_similar(movies, top_n)

    # Check cache
    cached = cache.get(cache_key)
    if cached is not None:
        logger.info("Cache HIT for similar: %s", cache_key)
        return cached

    # Compute
    svc = get_recommendation_service()
    recs = svc.recommend_similar(movies, top_n=top_n)
    result = {"recommendations": [r.model_dump() for r in recs]}

    # Cache
    cache.set(cache_key, result, TTL_SIMILAR)
    logger.info("Cache MISS for similar: %s (cached for %ds)", cache_key, TTL_SIMILAR)

    return result


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
    cache = get_redis_cache()
    user_id_for_cache = user.movielens_user_id if user is not None else None
    cache_key = cache.key_homepage(user_id_for_cache)

    # Check cache
    cached = cache.get(cache_key)
    if cached is not None:
        logger.info("Cache HIT for homepage: %s", cache_key)
        return cached

    # Compute (this is the slow path — ~98s on first call)
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

    result = {
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

    # Cache the result
    cache.set(cache_key, result, TTL_HOMEPAGE)
    logger.info("Cache MISS for homepage: %s (cached for %ds)", cache_key, TTL_HOMEPAGE)

    return result
