"""
Dependency injection for the FastAPI application.

All service singletons are created here.  Routers use ``get_*()``
functions to access them.  ``get_current_user`` and
``get_optional_user`` are FastAPI ``Depends()`` callables that
extract the JWT and resolve the user profile.

Phase 7: Swapped InMemoryUserRepository → PostgresUserRepository.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from recommendation.db.postgres_repository import PostgresUserRepository
from recommendation.db.redis_cache import RedisCache
from recommendation.user.profile_service import ProfileService
from recommendation.user.onboarding import OnboardingService
from recommendation.user.interaction_service import InteractionService
from recommendation.user.schemas import UserProfile
from recommendation.services.recommendation_service import RecommendationService
from recommendation.homepage.orchestrator import HomepageOrchestrator
from api.auth.jwt_handler import verify_token


# ── Singletons ──────────────────────────────────────────────────────
# Created once at module import time.  FastAPI's DI is synchronous
# for these (no async overhead).

_user_repo = PostgresUserRepository()
_profile_service = ProfileService(_user_repo)
_onboarding_service = OnboardingService(_user_repo, _profile_service)
_interaction_service = InteractionService(_user_repo)
_recommendation_service = RecommendationService()
_homepage_orchestrator = HomepageOrchestrator()
_redis_cache = RedisCache()

security = HTTPBearer(auto_error=False)


# ── Service accessors ──────────────────────────────────────────────

def get_user_repo() -> PostgresUserRepository:
    return _user_repo


def get_redis_cache() -> RedisCache:
    return _redis_cache


def get_profile_service() -> ProfileService:
    return _profile_service


def get_onboarding_service() -> OnboardingService:
    return _onboarding_service


def get_interaction_service() -> InteractionService:
    return _interaction_service


def get_recommendation_service() -> RecommendationService:
    return _recommendation_service


def get_homepage_orchestrator() -> HomepageOrchestrator:
    return _homepage_orchestrator


# ── Auth dependencies ──────────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserProfile:
    """Required auth — raises 401 if no valid JWT."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = verify_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = _user_repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserProfile | None:
    """Optional auth — returns None for anonymous requests."""
    if credentials is None:
        return None

    user_id = verify_token(credentials.credentials)
    if user_id is None:
        return None

    return _user_repo.get_by_id(user_id)
