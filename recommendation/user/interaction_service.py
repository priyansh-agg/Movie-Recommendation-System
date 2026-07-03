"""
Interaction service — tracks all user–movie interactions.

Every mutation (rate, like, dislike, watchlist, watched) is recorded
as an ``Interaction`` log entry so we can replay history, compute
time-weighted preferences, and feed future ML pipelines.
"""

import time

from recommendation.user.repository import UserRepository
from recommendation.user.schemas import Interaction


class InteractionService:
    """Records and queries user–movie interactions."""

    def __init__(self, repo: UserRepository):
        self._repo = repo

    # ── Internal helper ────────────────────────────────────────────

    def _add_interaction(self, user_id, tmdb_id, interaction_type, value=None):
        profile = self._repo.get_by_id(user_id)
        if profile is None:
            raise ValueError("User not found")

        profile.interactions.append(
            Interaction(
                tmdb_id=tmdb_id,
                interaction_type=interaction_type,
                value=value,
                timestamp=time.time(),
            )
        )
        return profile

    # ── Public API ─────────────────────────────────────────────────

    def rate_movie(self, user_id: int, tmdb_id: int, rating_value: float):
        """Rate a movie (0.5–5.0).  Auto-likes at 4.0+, auto-dislikes at 2.0-."""
        if not 0.5 <= rating_value <= 5.0:
            raise ValueError("Rating must be between 0.5 and 5.0")

        profile = self._add_interaction(
            user_id, tmdb_id, "rating", rating_value
        )
        profile.ratings[tmdb_id] = rating_value

        # Auto-like high ratings
        if rating_value >= 4.0 and tmdb_id not in profile.liked:
            profile.liked.append(tmdb_id)

        # Auto-dislike low ratings
        if rating_value <= 2.0 and tmdb_id not in profile.disliked:
            profile.disliked.append(tmdb_id)

        return self._repo.update(profile)

    def like_movie(self, user_id: int, tmdb_id: int):
        profile = self._add_interaction(user_id, tmdb_id, "like")
        if tmdb_id not in profile.liked:
            profile.liked.append(tmdb_id)
        if tmdb_id in profile.disliked:
            profile.disliked.remove(tmdb_id)
        return self._repo.update(profile)

    def dislike_movie(self, user_id: int, tmdb_id: int):
        profile = self._add_interaction(user_id, tmdb_id, "dislike")
        if tmdb_id not in profile.disliked:
            profile.disliked.append(tmdb_id)
        if tmdb_id in profile.liked:
            profile.liked.remove(tmdb_id)
        return self._repo.update(profile)

    def add_to_watchlist(self, user_id: int, tmdb_id: int):
        profile = self._add_interaction(user_id, tmdb_id, "watchlist_add")
        if tmdb_id not in profile.watchlist:
            profile.watchlist.append(tmdb_id)
        return self._repo.update(profile)

    def remove_from_watchlist(self, user_id: int, tmdb_id: int):
        profile = self._add_interaction(user_id, tmdb_id, "watchlist_remove")
        if tmdb_id in profile.watchlist:
            profile.watchlist.remove(tmdb_id)
        return self._repo.update(profile)

    def mark_watched(self, user_id: int, tmdb_id: int):
        """Add to watch history (most-recent first, deduped)."""
        profile = self._add_interaction(user_id, tmdb_id, "watched")
        if tmdb_id in profile.watch_history:
            profile.watch_history.remove(tmdb_id)
        profile.watch_history.insert(0, tmdb_id)
        return self._repo.update(profile)

    def get_watch_history(self, user_id: int, limit: int = 50) -> list[int]:
        profile = self._repo.get_by_id(user_id)
        if profile is None:
            return []
        return profile.watch_history[:limit]
