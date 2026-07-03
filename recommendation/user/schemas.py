"""
User domain models.

All user-related state is defined here.  These models are used by
the repository layer (in-memory now, PostgreSQL in Phase 7) and
serialised to/from the API layer.
"""

import time
from typing import Optional

from pydantic import BaseModel, Field


class UserPreferences(BaseModel):
    """Extracted taste profile — computed from onboarding + interactions."""

    favorite_genres: list[str] = Field(default_factory=list)
    favorite_movies: list[int] = Field(default_factory=list)  # tmdbIds
    disliked_genres: list[str] = Field(default_factory=list)


class Interaction(BaseModel):
    """Single user–movie interaction event (immutable log entry)."""

    tmdb_id: int
    interaction_type: str  # rating | like | dislike | watchlist_add | watchlist_remove | watched
    value: Optional[float] = None  # rating 0.5–5.0, or None
    timestamp: float = Field(default_factory=time.time)


class UserProfile(BaseModel):
    """
    Complete user state.

    This is the single source of truth for a user.  The repository
    stores and retrieves instances of this model.
    """

    id: int
    email: str
    username: str
    hashed_password: str

    # Maps to MovieLens userId for collaborative filtering.
    # None for users who registered through the app (cold-start).
    movielens_user_id: Optional[int] = None

    preferences: UserPreferences = Field(default_factory=UserPreferences)

    watch_history: list[int] = Field(default_factory=list)   # tmdbIds, most-recent first
    watchlist: list[int] = Field(default_factory=list)        # tmdbIds
    ratings: dict[int, float] = Field(default_factory=dict)   # tmdbId → rating
    liked: list[int] = Field(default_factory=list)            # tmdbIds
    disliked: list[int] = Field(default_factory=list)         # tmdbIds
    interactions: list[Interaction] = Field(default_factory=list)

    onboarded: bool = False
    created_at: float = Field(default_factory=time.time)
