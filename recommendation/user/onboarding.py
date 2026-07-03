"""
Onboarding service.

Guides new users through selecting 10+ movies so the system can
build an initial taste profile before showing personalised content.
"""

from recommendation.user.repository import UserRepository
from recommendation.user.profile_service import ProfileService
from recommendation.content_based.loader import (
    movie_titles,
    rating,
    metadata_lookup,
)
from recommendation.services.poster_service import fetch_poster


class OnboardingService:
    """Handles the onboarding flow for new users."""

    MINIMUM_SELECTIONS = 10

    def __init__(self, repo: UserRepository, profile_service: ProfileService):
        self._repo = repo
        self._profile_service = profile_service

    def get_onboarding_movies(self, count: int = 50) -> list[dict]:
        """
        Return a diverse set of popular movies for the selection UI.

        Strategy: rank by popularity, but cap each genre so the list
        isn't dominated by a single category.
        """
        scored: list[dict] = []

        for idx in range(len(movie_titles)):
            tmdb_id = int(movie_titles.iloc[idx]["id"])
            meta = metadata_lookup.get(tmdb_id)
            if meta is None:
                continue

            popularity = float(rating[idx][1])
            scored.append(
                {
                    "tmdb_id": tmdb_id,
                    "title": movie_titles.iloc[idx]["title"],
                    "poster": fetch_poster(tmdb_id),
                    "genres": str(meta.get("genres", "")),
                    "popularity": popularity,
                }
            )

        scored.sort(key=lambda x: x["popularity"], reverse=True)

        # Diversity cap: no genre gets more than count/5 slots.
        max_per_genre = max(count // 5, 3)
        genre_counts: dict[str, int] = {}
        selected: list[dict] = []

        for movie in scored:
            if len(selected) >= count:
                break

            genre_tokens = [g for g in movie["genres"].split() if g]
            if not genre_tokens:
                # Untagged movie — always include if popular
                selected.append(movie)
                continue

            if all(
                genre_counts.get(g, 0) < max_per_genre for g in genre_tokens
            ):
                selected.append(movie)
                for g in genre_tokens:
                    genre_counts[g] = genre_counts.get(g, 0) + 1

        return selected

    def complete_onboarding(
        self, user_id: int, selected_tmdb_ids: list[int]
    ) -> "UserProfile":
        """
        Process onboarding selections.

        1. Validates minimum selection count.
        2. Extracts genre preferences from selected movies.
        3. Adds selections as liked movies.
        4. Marks the user as onboarded.
        """
        if len(selected_tmdb_ids) < self.MINIMUM_SELECTIONS:
            raise ValueError(
                f"Please select at least {self.MINIMUM_SELECTIONS} movies. "
                f"You selected {len(selected_tmdb_ids)}."
            )

        profile = self._repo.get_by_id(user_id)
        if profile is None:
            raise ValueError("User not found")

        # Extract preferences from selected movies
        preferences = self._profile_service.extract_preferences(
            selected_tmdb_ids
        )
        profile.preferences = preferences
        profile.onboarded = True

        # Add selections as liked movies (dedup)
        existing = set(profile.liked)
        for tmdb_id in selected_tmdb_ids:
            if tmdb_id not in existing:
                profile.liked.append(tmdb_id)
                existing.add(tmdb_id)

        return self._repo.update(profile)
