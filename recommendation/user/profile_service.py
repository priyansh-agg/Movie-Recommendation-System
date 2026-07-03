"""
Profile service — profile CRUD and preference extraction.

Sits between the API layer and the repository.  Handles business
logic like computing genre preferences from a set of movies.
"""

from recommendation.user.repository import UserRepository
from recommendation.user.schemas import UserProfile, UserPreferences
from recommendation.content_based.loader import metadata_lookup, movie_to_index


class ProfileService:
    """Profile management and preference extraction."""

    def __init__(self, repo: UserRepository):
        self._repo = repo

    # ── Read ────────────────────────────────────────────────────────

    def get_profile(self, user_id: int) -> UserProfile | None:
        return self._repo.get_by_id(user_id)

    # ── Preference extraction ──────────────────────────────────────

    def extract_preferences(self, tmdb_ids: list[int]) -> UserPreferences:
        """
        Analyse a set of movies to compute a genre-frequency profile.

        Used during onboarding (user picks 10+ movies) and can be
        re-run whenever the liked set grows significantly.
        """
        genre_counts: dict[str, int] = {}

        for tmdb_id in tmdb_ids:
            meta = metadata_lookup.get(tmdb_id)
            if meta is None:
                continue

            genres_str = str(meta.get("genres", ""))
            # Genre strings are space-separated lowercase tokens
            # e.g. "action adventure sciencefiction"
            for genre_token in genres_str.split():
                if genre_token:
                    genre_counts[genre_token] = genre_counts.get(genre_token, 0) + 1

        # Top-5 genres by frequency
        sorted_genres = sorted(
            genre_counts.items(), key=lambda x: x[1], reverse=True
        )
        favorite_genres = [g for g, _ in sorted_genres[:5]]

        return UserPreferences(
            favorite_genres=favorite_genres,
            favorite_movies=list(tmdb_ids),
        )

    # ── Liked titles for hybrid engine ─────────────────────────────

    def get_liked_movie_titles(self, user_id: int) -> list[str]:
        """
        Resolve a user's liked + favourite tmdbIds into title strings
        that the hybrid engine can consume.

        Only returns titles that exist in the content model.
        """
        profile = self._repo.get_by_id(user_id)
        if profile is None:
            return []

        tmdb_ids = list(
            set(profile.liked + profile.preferences.favorite_movies)
        )

        titles: list[str] = []
        for tmdb_id in tmdb_ids:
            meta = metadata_lookup.get(tmdb_id)
            if meta is None:
                continue
            title = meta.get("title")
            if title and title in movie_to_index:
                titles.append(title)

        return titles

    # ── Manual preference override ─────────────────────────────────

    def update_preferences(
        self, user_id: int, preferences: UserPreferences
    ) -> UserProfile | None:
        profile = self._repo.get_by_id(user_id)
        if profile is None:
            return None
        profile.preferences = preferences
        return self._repo.update(profile)
