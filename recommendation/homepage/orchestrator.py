"""
Netflix-style homepage orchestrator.

Assembles all homepage sections, deduplicates movies across them,
and returns the final ordered list of sections ready for the frontend.

Phase 4 Enhancement: now accepts an optional UserProfile to build
user-aware sections (continue watching, top rated by user, watchlist,
preference-driven genres).
"""

from recommendation.common.schemas import HomepageSection
from recommendation.homepage.sections import (
    build_top_picks,
    build_because_you_watched,
    build_trending,
    build_popular,
    build_genre_section,
    build_new_releases,
    build_continue_watching,
    build_top_rated_by_user,
    build_top_rated_editorial,
    build_watchlist_section,
)
from recommendation.homepage.deduplicator import deduplicate_sections
from recommendation.config import (
    HOMEPAGE_GENRES,
    BECAUSE_YOU_WATCHED_MAX_MOVIES,
    GENRE_SEARCH_TERMS,
)


class HomepageOrchestrator:
    """
    Builds the complete Netflix-style homepage for a user.

    Section priority order (highest first):
        1. Continue Watching       (from watch history)
        2. Top Picks For You       (hybrid, personalised)
        3. Because You Watched X   (content, per recent movie)
        4. Because You Rated Highly (content from top ratings)
        5. Your Watchlist          (quick-access row)
        6. Trending Now            (recent rating activity)
        7. Popular This Week       (all-time popularity)
        8. Genre rows              (user prefs first, then defaults)
        9. New Releases            (by release year)
       10. Top Rated               (editorial, all-time)

    Higher-priority sections keep their movies during deduplication.
    Anonymous users (no user_id, no liked_movies) still see the
    universal sections (trending, popular, genres, new releases, top rated).
    """

    def get_homepage(
        self,
        user_id=None,
        liked_movies=None,
        user_profile=None,
    ) -> list[HomepageSection]:
        """
        Generate the full homepage.

        Parameters
        ----------
        user_id : int | None
            MovieLens user ID.  ``None`` for anonymous users.
        liked_movies : list[str] | None
            Movie titles the user has explicitly liked.
        user_profile : UserProfile | None
            Full user profile for enhanced personalisation.
            When provided, enables: continue watching, top rated by user,
            watchlist row, and preference-driven genre selection.

        Returns
        -------
        list[HomepageSection]
            Ordered, deduplicated homepage sections.
        """

        sections: list[HomepageSection] = []

        # -- Personalised sections (require user data) -------------------

        if user_profile is not None:
            # Continue Watching (from watch history)
            if user_profile.watch_history:
                cw = build_continue_watching(user_profile.watch_history)
                if cw.movies:
                    sections.append(cw)

        if liked_movies:
            # Top Picks (hybrid engine)
            sections.append(build_top_picks(user_id, liked_movies))

            # "Because You Watched" rows for the most recent N movies
            recent_movies = liked_movies[-BECAUSE_YOU_WATCHED_MAX_MOVIES:]
            for movie_title in recent_movies:
                section = build_because_you_watched(movie_title)
                if section.movies:
                    sections.append(section)

        elif user_id is not None:
            # User has rating history but no explicit liked movies.
            sections.append(build_top_picks(user_id, liked_movies=None))

        if user_profile is not None:
            # Because You Rated Highly (content recs from top-rated)
            if user_profile.ratings:
                rated = build_top_rated_by_user(user_profile.ratings)
                if rated.movies:
                    sections.append(rated)

            # Your Watchlist (quick-access row)
            if user_profile.watchlist:
                wl = build_watchlist_section(user_profile.watchlist)
                if wl.movies:
                    sections.append(wl)

        # -- Universal sections (all users see these) --------------------
        sections.append(build_trending())
        sections.append(build_popular())

        # -- Genre sections ----------------------------------------------
        # Use user's favourite genres first, then fall back to defaults
        genres_to_show = list(HOMEPAGE_GENRES)  # start with defaults

        if user_profile is not None and user_profile.preferences.favorite_genres:
            # Map user's preference tokens back to display names
            user_genres = []
            reverse_map = {}
            for display_name, tokens in GENRE_SEARCH_TERMS.items():
                for token in tokens:
                    reverse_map[token] = display_name

            for pref_token in user_profile.preferences.favorite_genres:
                display = reverse_map.get(pref_token, pref_token.capitalize())
                if display not in user_genres:
                    user_genres.append(display)

            # User genres first, then remaining defaults
            seen = set(user_genres)
            for default_genre in HOMEPAGE_GENRES:
                if default_genre not in seen:
                    user_genres.append(default_genre)
            genres_to_show = user_genres[:6]  # cap at 6 genre rows

        for genre in genres_to_show:
            section = build_genre_section(genre)
            if section.movies:
                sections.append(section)

        # -- Editorial sections ------------------------------------------
        sections.append(build_new_releases())
        sections.append(build_top_rated_editorial())

        # -- Deduplicate across all sections -----------------------------
        return deduplicate_sections(sections)
