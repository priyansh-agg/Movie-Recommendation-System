"""
Netflix-style homepage orchestrator.

Assembles all homepage sections, deduplicates movies across them,
and returns the final ordered list of sections ready for the frontend.
"""

from recommendation.common.schemas import HomepageSection
from recommendation.homepage.sections import (
    build_top_picks,
    build_because_you_watched,
    build_trending,
    build_popular,
    build_genre_section,
    build_new_releases,
)
from recommendation.homepage.deduplicator import deduplicate_sections
from recommendation.config import (
    HOMEPAGE_GENRES,
    BECAUSE_YOU_WATCHED_MAX_MOVIES,
)


class HomepageOrchestrator:
    """
    Builds the complete Netflix-style homepage for a user.

    Section priority order (highest first):
        1. Top Picks For You        (hybrid, personalised)
        2. Because You Watched X    (content, per liked movie)
        3. Trending Now             (recent rating activity)
        4. Popular This Week        (all-time popularity)
        5. Genre rows               (Action, Comedy, SciFi, Drama)
        6. New Releases             (sorted by release year)

    Higher-priority sections keep their movies during deduplication.
    Anonymous users (no user_id, no liked_movies) still see the
    universal sections (trending, popular, genres, new releases).
    """

    def get_homepage(
        self,
        user_id=None,
        liked_movies=None,
    ) -> list[HomepageSection]:
        """
        Generate the full homepage.

        Parameters
        ----------
        user_id : int | None
            MovieLens user ID.  ``None`` for anonymous users.
        liked_movies : list[str] | None
            Movie titles the user has explicitly liked.

        Returns
        -------
        list[HomepageSection]
            Ordered, deduplicated homepage sections.
        """

        sections: list[HomepageSection] = []

        # ── Personalised sections (only if we have taste data) ──────
        if liked_movies:
            sections.append(
                build_top_picks(user_id, liked_movies)
            )

            # "Because You Watched" rows for the most recent N movies.
            recent_movies = liked_movies[-BECAUSE_YOU_WATCHED_MAX_MOVIES:]
            for movie_title in recent_movies:
                section = build_because_you_watched(movie_title)
                # Only add if the builder returned movies.
                if section.movies:
                    sections.append(section)

        elif user_id is not None:
            # User has rating history but no explicit liked movies.
            # Still generate hybrid recs from collaborative data.
            sections.append(
                build_top_picks(user_id, liked_movies=None)
            )

        # ── Universal sections (all users see these) ────────────────
        sections.append(build_trending())
        sections.append(build_popular())

        # ── Genre sections ──────────────────────────────────────────
        for genre in HOMEPAGE_GENRES:
            section = build_genre_section(genre)
            if section.movies:
                sections.append(section)

        # ── New Releases ────────────────────────────────────────────
        sections.append(build_new_releases())

        # ── Deduplicate across all sections ─────────────────────────
        return deduplicate_sections(sections)
