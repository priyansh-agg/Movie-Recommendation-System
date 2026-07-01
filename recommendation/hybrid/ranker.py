from recommendation.common.schemas import Recommendation
from recommendation.config import (
    HYBRID_WEIGHT_CONTENT,
    HYBRID_WEIGHT_COLLABORATIVE,
    HYBRID_WEIGHT_POPULARITY,
)


def rank_recommendations(
    merged: list[Recommendation],
    norm_content: dict[int, float],
    norm_collab: dict[int, float],
    norm_popularity: dict[int, float],
    top_n: int = 10,
    *,
    weight_content: float = HYBRID_WEIGHT_CONTENT,
    weight_collaborative: float = HYBRID_WEIGHT_COLLABORATIVE,
    weight_popularity: float = HYBRID_WEIGHT_POPULARITY,
) -> list[Recommendation]:
    """
    Compute hybrid scores and return top-N ranked recommendations.

    Each recommendation's hybrid score is a weighted sum of its
    normalized content, collaborative, and popularity scores.

    Normalized score dicts map ``tmdbId → float ∈ [0, 1]``.
    Movies missing from a dict receive ``0.0`` for that component
    (not penalized, not boosted) — this handles cold-start gracefully
    where a movie only has content **or** collaborative data.

    The hybrid score is written into ``rec.scores.hybrid``.
    Raw scores (``content``, ``collaborative``, ``popularity``) are
    **never** modified.

    Parameters
    ----------
    merged : list[Recommendation]
        Output of the merger — the combined candidate pool.
    norm_content : dict[int, float]
        Normalized content scores keyed by tmdbId.
    norm_collab : dict[int, float]
        Normalized collaborative scores keyed by tmdbId.
    norm_popularity : dict[int, float]
        Normalized popularity scores keyed by tmdbId.
    top_n : int
        How many recommendations to return.
    weight_content : float
        Weight for the content score component.
    weight_collaborative : float
        Weight for the collaborative score component.
    weight_popularity : float
        Weight for the popularity score component.

    Returns
    -------
    list[Recommendation]
        Top-N recommendations sorted by hybrid score descending.
    """

    for rec in merged:
        tmdb_id = rec.tmdbId

        c_val = norm_content.get(tmdb_id, 0.0)
        cf_val = norm_collab.get(tmdb_id, 0.0)
        p_val = norm_popularity.get(tmdb_id, 0.0)

        rec.scores.hybrid = (
            weight_content * c_val
            + weight_collaborative * cf_val
            + weight_popularity * p_val
        )

    merged.sort(key=lambda r: r.scores.hybrid or 0.0, reverse=True)

    return merged[:top_n]
