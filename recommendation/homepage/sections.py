"""
Netflix-style homepage section builders.

Each function generates one **independent** section.  No section
depends on another.  The orchestrator assembles them and the
deduplicator removes cross-section duplicates.

Section types
-------------
personalized  -- driven by the user's taste profile
trending      -- based on recent rating activity
genre         -- filtered by genre tag, sorted by popularity
editorial     -- curated lists (popular, new releases, top rated)
"""

import re
import pandas as pd

from recommendation.common.schemas import HomepageSection
from recommendation.common.builder import build_recommendation
from recommendation.content_based.loader import (
    movie_titles,
    rating,
    metadata_lookup,
    movie_to_index,
)
from recommendation.collaborative.loader import load_ratings
from recommendation.mapping.loader import movie_to_tmdb_id
from recommendation.services.poster_service import fetch_poster
from recommendation.hybrid.recommender import recommend as hybrid_recommend
from recommendation.content_based.recommender import recommend as content_recommend
from recommendation.config import (
    HOMEPAGE_SECTION_SIZE,
    BECAUSE_YOU_WATCHED_SIZE,
    TRENDING_RECENCY_FRACTION,
    GENRE_SEARCH_TERMS,
)


# -- Lazy-loaded module-level data -------------------------------------------

_ratings_df = None


def _get_ratings_df():
    global _ratings_df
    if _ratings_df is None:
        _ratings_df = load_ratings()
    return _ratings_df


# -- Helpers -----------------------------------------------------------------

_YEAR_RE = re.compile(r"\((\d{4})\)\s*$")


def _extract_year(metadata, title):
    """Extract release year from metadata or title string."""
    release_date = metadata.get("release_date") if metadata else None
    if release_date and isinstance(release_date, str) and len(release_date) >= 4:
        try:
            return int(release_date[:4])
        except ValueError:
            pass
    match = _YEAR_RE.search(str(title))
    if match:
        return int(match.group(1))
    return None


def _build_section_rec(idx, tmdb_id, metadata, source, reason_text,
                       popularity=None):
    """Convenience wrapper for building a Recommendation for a section."""
    return build_recommendation(
        tmdb_id=tmdb_id,
        title=metadata.get("title", movie_titles.iloc[idx]["title"]),
        poster=fetch_poster(tmdb_id),
        metadata=metadata if metadata else {},
        explanation={
            "engine": source,
            "reasons": [reason_text] if reason_text else [],
        },
        popularity_score=float(popularity) if popularity is not None else None,
        source=source,
    )


# ============================================================================
# Existing section builders (from Phase 2)
# ============================================================================

def build_top_picks(user_id, liked_movies, size=HOMEPAGE_SECTION_SIZE):
    """
    Top personalised picks via the hybrid engine.

    This is the highest-priority section on the homepage -- it
    blends content and collaborative signals through the full
    hybrid pipeline.
    """
    movies = hybrid_recommend(
        user_id=user_id,
        liked_movies=liked_movies,
        top_n=size,
    )
    return HomepageSection(
        section_id="top_picks",
        title="Top Picks For You",
        section_type="personalized",
        movies=movies,
    )


def build_because_you_watched(movie_title, size=BECAUSE_YOU_WATCHED_SIZE):
    """
    Content-based recommendations anchored to a single movie.

    Produces one "Because You Watched <Movie>" row.
    """
    movies = content_recommend([movie_title], top_n=size)
    safe_id = re.sub(r"[^a-z0-9]+", "_", movie_title.lower())[:40]
    return HomepageSection(
        section_id=f"because_you_watched_{safe_id}",
        title=f"Because You Watched {movie_title}",
        section_type="personalized",
        movies=movies,
    )


def build_trending(size=HOMEPAGE_SECTION_SIZE):
    """
    Movies trending by recent rating activity.

    Uses MovieLens timestamps to simulate recency: movies with the
    most ratings in the most recent fraction of the timestamp range.
    """
    ratings_df = _get_ratings_df()

    # Ensure timestamp is numeric (large dataset CSVs may load as strings)
    ratings_df["timestamp"] = pd.to_numeric(ratings_df["timestamp"], errors="coerce")

    max_ts = ratings_df["timestamp"].max()
    min_ts = ratings_df["timestamp"].min()
    cutoff = max_ts - (max_ts - min_ts) * TRENDING_RECENCY_FRACTION

    recent = ratings_df[ratings_df["timestamp"] >= cutoff]

    trending_counts = (
        recent
        .groupby("movieId")
        .size()
        .reset_index(name="recent_count")
        .sort_values("recent_count", ascending=False)
    )

    movies = []
    for _, row in trending_counts.iterrows():
        if len(movies) >= size:
            break
        movie_id = int(row["movieId"])
        tmdb_id = movie_to_tmdb_id(movie_id)
        if tmdb_id is None:
            continue
        metadata = metadata_lookup.get(tmdb_id)
        if metadata is None:
            continue
        count = int(row["recent_count"])
        movies.append(
            _build_section_rec(
                idx=0,
                tmdb_id=tmdb_id,
                metadata=metadata,
                source="trending",
                reason_text=f"Trending with {count} recent ratings",
                popularity=float(count),
            )
        )

    return HomepageSection(
        section_id="trending",
        title="Trending Now",
        section_type="trending",
        movies=movies,
    )


def build_popular(size=HOMEPAGE_SECTION_SIZE):
    """
    All-time popular movies.

    Score = 0.4 x vote_avg + 0.6 x popularity  (from the content
    model's pre-computed rating array).
    """
    scored = []
    for idx in range(len(movie_titles)):
        vote_avg = rating[idx][0]
        popularity = rating[idx][1]
        score = 0.4 * vote_avg + 0.6 * popularity
        scored.append((idx, score, popularity))

    scored.sort(key=lambda x: x[1], reverse=True)

    movies = []
    for idx, _score, popularity in scored:
        if len(movies) >= size:
            break
        tmdb_id = int(movie_titles.iloc[idx]["id"])
        metadata = metadata_lookup.get(tmdb_id)
        if metadata is None:
            continue
        movies.append(
            _build_section_rec(
                idx=idx,
                tmdb_id=tmdb_id,
                metadata=metadata,
                source="popular",
                reason_text="Highly rated and widely popular",
                popularity=popularity,
            )
        )

    return HomepageSection(
        section_id="popular",
        title="Popular This Week",
        section_type="editorial",
        movies=movies,
    )


def build_genre_section(genre, size=HOMEPAGE_SECTION_SIZE):
    """
    Movies filtered by genre tag, sorted by popularity.

    Uses the genre search terms from config to handle multi-token
    genres (e.g. "SciFi" -> ["sciencefiction", "scifi", "science"]).
    """
    search_terms = GENRE_SEARCH_TERMS.get(genre, [genre.lower()])

    candidates = []
    for idx in range(len(movie_titles)):
        tmdb_id = int(movie_titles.iloc[idx]["id"])
        metadata = metadata_lookup.get(tmdb_id)
        if metadata is None:
            continue
        genres_str = str(metadata.get("genres", "")).lower()
        if not any(term in genres_str for term in search_terms):
            continue
        popularity = rating[idx][1]
        candidates.append((idx, tmdb_id, metadata, popularity))

    candidates.sort(key=lambda x: x[3], reverse=True)

    movies = []
    for idx, tmdb_id, metadata, popularity in candidates[:size]:
        movies.append(
            _build_section_rec(
                idx=idx,
                tmdb_id=tmdb_id,
                metadata=metadata,
                source="genre",
                reason_text=f"Top {genre} movie",
                popularity=popularity,
            )
        )

    return HomepageSection(
        section_id=f"genre_{genre.lower()}",
        title=f"{genre} Movies",
        section_type="genre",
        movies=movies,
    )


def build_new_releases(size=HOMEPAGE_SECTION_SIZE):
    """
    Most recent movies by release year.

    Extracts year from metadata ``release_date`` or falls back to
    parsing the title string.  Sorted by year descending, then
    popularity within the same year.
    """
    candidates = []
    for idx in range(len(movie_titles)):
        tmdb_id = int(movie_titles.iloc[idx]["id"])
        title = movie_titles.iloc[idx]["title"]
        metadata = metadata_lookup.get(tmdb_id)
        year = _extract_year(metadata, title)
        if year is None:
            continue
        popularity = rating[idx][1]
        candidates.append((idx, tmdb_id, metadata, year, popularity))

    candidates.sort(key=lambda x: (x[3], x[4]), reverse=True)

    movies = []
    for idx, tmdb_id, metadata, year, popularity in candidates[:size]:
        movies.append(
            _build_section_rec(
                idx=idx,
                tmdb_id=tmdb_id,
                metadata=metadata if metadata else {},
                source="new_releases",
                reason_text=f"Released in {year}",
                popularity=popularity,
            )
        )

    return HomepageSection(
        section_id="new_releases",
        title="New Releases",
        section_type="editorial",
        movies=movies,
    )


# ============================================================================
# Phase 4 -- New section builders (user-profile-aware)
# ============================================================================

def build_continue_watching(watch_history, size=HOMEPAGE_SECTION_SIZE):
    """
    "Continue Watching" row from the user's watch history.

    Shows the most recently watched movies (most recent first).
    The frontend can style these as partially-watched cards.
    """
    if not watch_history:
        return HomepageSection(
            section_id="continue_watching",
            title="Continue Watching",
            section_type="personalized",
            movies=[],
        )

    movies = []
    for tmdb_id in watch_history[:size]:
        metadata = metadata_lookup.get(tmdb_id)
        if metadata is None:
            continue
        movies.append(
            _build_section_rec(
                idx=0,
                tmdb_id=tmdb_id,
                metadata=metadata,
                source="continue_watching",
                reason_text="Recently watched",
            )
        )

    return HomepageSection(
        section_id="continue_watching",
        title="Continue Watching",
        section_type="personalized",
        movies=movies,
    )


def build_top_rated_by_user(user_ratings, size=HOMEPAGE_SECTION_SIZE):
    """
    "Because You Rated Highly" -- content recommendations seeded
    from the user's highest-rated movies.

    Takes the user's top 3 rated movies, generates content recs
    for each, and merges them into a single section.
    """
    if not user_ratings:
        return HomepageSection(
            section_id="top_rated_by_user",
            title="Because You Rated Highly",
            section_type="personalized",
            movies=[],
        )

    # Sort ratings descending, take top 3 movies
    sorted_ratings = sorted(
        user_ratings.items(), key=lambda x: x[1], reverse=True
    )
    top_rated_ids = [tmdb_id for tmdb_id, _ in sorted_ratings[:3]]

    # Resolve to titles for the content engine
    seed_titles = []
    for tmdb_id in top_rated_ids:
        meta = metadata_lookup.get(tmdb_id)
        if meta and meta.get("title") and meta["title"] in movie_to_index:
            seed_titles.append(meta["title"])

    if not seed_titles:
        return HomepageSection(
            section_id="top_rated_by_user",
            title="Because You Rated Highly",
            section_type="personalized",
            movies=[],
        )

    movies = content_recommend(seed_titles, top_n=size)

    return HomepageSection(
        section_id="top_rated_by_user",
        title="Because You Rated Highly",
        section_type="personalized",
        movies=movies,
    )


def build_top_rated_editorial(size=HOMEPAGE_SECTION_SIZE):
    """
    All-time top-rated movies (editorial, not personalised).

    Ranked purely by vote_average from the content model.
    """
    scored = []
    for idx in range(len(movie_titles)):
        vote_avg = rating[idx][0]
        popularity = rating[idx][1]
        # Only include movies with meaningful vote counts (popularity > threshold)
        if popularity < 0.01:
            continue
        scored.append((idx, vote_avg, popularity))

    scored.sort(key=lambda x: x[1], reverse=True)

    movies = []
    for idx, vote_avg, popularity in scored[:size]:
        tmdb_id = int(movie_titles.iloc[idx]["id"])
        metadata = metadata_lookup.get(tmdb_id)
        if metadata is None:
            continue
        movies.append(
            _build_section_rec(
                idx=idx,
                tmdb_id=tmdb_id,
                metadata=metadata,
                source="top_rated",
                reason_text=f"Top rated with {vote_avg:.1f} average",
                popularity=popularity,
            )
        )

    return HomepageSection(
        section_id="top_rated",
        title="Top Rated",
        section_type="editorial",
        movies=movies,
    )


def build_watchlist_section(watchlist, size=HOMEPAGE_SECTION_SIZE):
    """
    User's watchlist as a homepage section for quick access.
    """
    if not watchlist:
        return HomepageSection(
            section_id="your_watchlist",
            title="Your Watchlist",
            section_type="personalized",
            movies=[],
        )

    movies = []
    for tmdb_id in watchlist[:size]:
        metadata = metadata_lookup.get(tmdb_id)
        if metadata is None:
            continue
        movies.append(
            _build_section_rec(
                idx=0,
                tmdb_id=tmdb_id,
                metadata=metadata,
                source="watchlist",
                reason_text="On your watchlist",
            )
        )

    return HomepageSection(
        section_id="your_watchlist",
        title="Your Watchlist",
        section_type="personalized",
        movies=movies,
    )
