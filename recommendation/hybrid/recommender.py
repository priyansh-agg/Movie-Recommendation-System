"""
Hybrid recommendation engine.

Orchestrates the full pipeline:
    Content candidates  ─┐
                          ├─ Merge ─→ Normalize ─→ Rank ─→ Top-N
    Collab candidates   ─┘

Cold-start strategy:
    • No user_id     → content-only with adjusted weights
    • No liked_movies → collab-only with adjusted weights
    • Neither         → empty list
"""

from recommendation.content_based.recommender import recommend as content_recommend
from recommendation.collaborative.recommender import recommend as collab_recommend
from recommendation.hybrid.merger import merge_recommendations
from recommendation.hybrid.normalizer import normalize_scores
from recommendation.hybrid.ranker import rank_recommendations
from recommendation.config import (
    CONTENT_CANDIDATES,
    COLLAB_CANDIDATES,
    HYBRID_WEIGHT_CONTENT,
    HYBRID_WEIGHT_COLLABORATIVE,
    HYBRID_WEIGHT_POPULARITY,
    CONTENT_ONLY_WEIGHT_CONTENT,
    CONTENT_ONLY_WEIGHT_POPULARITY,
    COLLAB_ONLY_WEIGHT_COLLABORATIVE,
    COLLAB_ONLY_WEIGHT_POPULARITY,
)


def recommend(user_id=None, liked_movies=None, top_n=10):
    """
    Generate hybrid recommendations by combining content-based and
    collaborative filtering engines.

    Pipeline
    --------
    1. Generate content candidates  (from ``liked_movies``)
    2. Generate collab candidates   (from ``user_id``)
    3. Merge by TMDB ID
    4. Normalize each score dimension independently
    5. Compute weighted hybrid score
    6. Return top-N ranked results

    Parameters
    ----------
    user_id : int | None
        MovieLens user ID.  ``None`` for anonymous / cold-start users.
    liked_movies : list[str] | None
        Movie titles the user has explicitly liked.
    top_n : int
        Number of recommendations to return.

    Returns
    -------
    list[Recommendation]
        Ranked hybrid recommendations.
    """

    if user_id is None and not liked_movies:
        return []

    # ── Stage 1: Generate candidates ────────────────────────────────
    content_candidates = []
    collab_candidates = []

    if liked_movies:
        content_candidates = content_recommend(
            liked_movies, top_n=CONTENT_CANDIDATES
        )

    if user_id is not None:
        try:
            collab_candidates = collab_recommend(
                user_id, top_n=COLLAB_CANDIDATES
            )
        except Exception:
            # User not found in training data — fall back gracefully.
            collab_candidates = []

    # ── Stage 2: Determine scoring mode ─────────────────────────────
    has_content = len(content_candidates) > 0
    has_collab = len(collab_candidates) > 0

    if not has_content and not has_collab:
        return []

    if has_content and has_collab:
        w_content = HYBRID_WEIGHT_CONTENT
        w_collab = HYBRID_WEIGHT_COLLABORATIVE
        w_popularity = HYBRID_WEIGHT_POPULARITY
    elif has_content:
        # Cold start: no collaborative data available.
        w_content = CONTENT_ONLY_WEIGHT_CONTENT
        w_collab = 0.0
        w_popularity = CONTENT_ONLY_WEIGHT_POPULARITY
    else:
        # No liked movies: collaborative only.
        w_content = 0.0
        w_collab = COLLAB_ONLY_WEIGHT_COLLABORATIVE
        w_popularity = COLLAB_ONLY_WEIGHT_POPULARITY

    # ── Stage 3: Merge ──────────────────────────────────────────────
    merged = merge_recommendations(content_candidates, collab_candidates)

    if not merged:
        return []

    # ── Stage 4: Normalize ──────────────────────────────────────────
    norm_content = normalize_scores(merged, "content")
    norm_collab = normalize_scores(merged, "collaborative")
    norm_popularity = normalize_scores(merged, "popularity")

    # ── Stage 5 & 6: Rank and return ────────────────────────────────
    return rank_recommendations(
        merged,
        norm_content,
        norm_collab,
        norm_popularity,
        top_n=top_n,
        weight_content=w_content,
        weight_collaborative=w_collab,
        weight_popularity=w_popularity,
    )
