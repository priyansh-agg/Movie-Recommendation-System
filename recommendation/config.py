"""
Central configuration for the recommendation system.

All tunable weights, thresholds, and constants live here.
Import from this module instead of hardcoding magic numbers.
"""

# ---------------------------------------------------------------------------
# Hybrid scoring weights (must sum to 1.0)
# ---------------------------------------------------------------------------
HYBRID_WEIGHT_CONTENT = 0.50
HYBRID_WEIGHT_COLLABORATIVE = 0.35
HYBRID_WEIGHT_POPULARITY = 0.15

# Fallback weights when only one engine produces candidates.
# Content-only: user has liked movies but no rating history (cold start).
CONTENT_ONLY_WEIGHT_CONTENT = 0.85
CONTENT_ONLY_WEIGHT_POPULARITY = 0.15

# Collab-only: user has rating history but no explicit liked movies.
COLLAB_ONLY_WEIGHT_COLLABORATIVE = 0.85
COLLAB_ONLY_WEIGHT_POPULARITY = 0.15

# ---------------------------------------------------------------------------
# Candidate generation
# ---------------------------------------------------------------------------
# Over-fetch so the merger has a rich pool before ranking trims it.
CONTENT_CANDIDATES = 30
COLLAB_CANDIDATES = 30

# Minimum cosine similarity to even consider a movie as a candidate.
CONTENT_MIN_THRESHOLD = 0.25

# ---------------------------------------------------------------------------
# Homepage
# ---------------------------------------------------------------------------
HOMEPAGE_SECTION_SIZE = 15
BECAUSE_YOU_WATCHED_SIZE = 10
BECAUSE_YOU_WATCHED_MAX_MOVIES = 3

# Trending window: top 20% most-recent timestamps in the dataset.
TRENDING_RECENCY_FRACTION = 0.20

# Genre sections to display on the homepage.
HOMEPAGE_GENRES = ["Action", "Comedy", "SciFi", "Drama"]

# Map display names -> search tokens for matching against metadata.
# Genres in the preprocessed metadata are lowercased, space-stripped tags
# (e.g. "sciencefiction").  Multiple tokens are OR-matched.
GENRE_SEARCH_TERMS = {
    "Action": ["action"],
    "Comedy": ["comedy"],
    "SciFi": ["sciencefiction", "scifi", "science"],
    "Drama": ["drama"],
    "Thriller": ["thriller"],
    "Romance": ["romance"],
    "Horror": ["horror"],
    "Animation": ["animation"],
    "Documentary": ["documentary"],
    "Crime": ["crime"],
    "Adventure": ["adventure"],
    "Fantasy": ["fantasy"],
}

# ---------------------------------------------------------------------------
# User Intelligence (Phase 3)
# ---------------------------------------------------------------------------
ONBOARDING_MOVIE_COUNT = 50
ONBOARDING_MIN_SELECTIONS = 10
AUTO_LIKE_THRESHOLD = 4.0
AUTO_DISLIKE_THRESHOLD = 2.0

# ---------------------------------------------------------------------------
# Evaluation (Phase 5)
# ---------------------------------------------------------------------------
EVAL_K_VALUES = [5, 10, 20]
EVAL_MAX_USERS = 50  # Limit for dev speed
EVAL_RELEVANCE_THRESHOLD = 4.0  # Rating >= this is "relevant"
