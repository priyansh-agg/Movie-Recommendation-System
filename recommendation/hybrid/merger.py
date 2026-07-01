from recommendation.common.schemas import Recommendation


def merge_recommendations(
    content: list[Recommendation],
    collaborative: list[Recommendation],
) -> list[Recommendation]:
    """
    Merge content-based and collaborative recommendations by TMDB ID.

    When the same movie appears in both lists, scores are combined
    into a single Recommendation object.  Content data takes priority
    for metadata and poster since it is richer.

    This function does NOT rank or normalize — it only merges.

    Parameters
    ----------
    content : list[Recommendation]
        Candidates from the content-based engine.
    collaborative : list[Recommendation]
        Candidates from the collaborative filtering engine.

    Returns
    -------
    list[Recommendation]
        De-duplicated, merged candidate pool.
    """

    merged: dict[int, Recommendation] = {}

    # Content goes in first — its metadata is richer.
    for movie in content:
        if movie.tmdbId is None:
            continue
        merged[movie.tmdbId] = movie

    for movie in collaborative:
        if movie.tmdbId is None:
            continue

        # New movie — just add it.
        if movie.tmdbId not in merged:
            merged[movie.tmdbId] = movie
            continue

        # Movie exists in both engines — combine scores.
        existing = merged[movie.tmdbId]
        existing.scores.collaborative = movie.scores.collaborative

        if existing.scores.popularity is None:
            existing.scores.popularity = movie.scores.popularity

        if not existing.metadata and movie.metadata:
            existing.metadata = movie.metadata

        if not existing.poster and movie.poster:
            existing.poster = movie.poster

        # Merge explanation reasons without duplicates.
        existing.explanation.reasons.extend(
            reason
            for reason in movie.explanation.reasons
            if reason not in existing.explanation.reasons
        )

    # Tag every merged candidate as coming through the hybrid pipeline.
    for rec in merged.values():
        rec.source = "hybrid"

    return list(merged.values())