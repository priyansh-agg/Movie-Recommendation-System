from recommendation.common.schemas import (
    Recommendation,
    Scores,
    Explanation,
)


def build_recommendation(
    *,
    movie_id=None,
    tmdb_id=None,
    title,
    poster,
    metadata,
    explanation,
    content_score=None,
    collaborative_score=None,
    popularity_score=None,
    hybrid_score=None,
    source=None
):

    return Recommendation(
        movieId=movie_id,
        tmdbId=tmdb_id,
        title=title,
        poster=poster,

        scores=Scores(
            content=content_score,
            collaborative=collaborative_score,
            popularity=popularity_score,
            hybrid=hybrid_score,
        ),

        metadata=metadata,

        explanation=Explanation(
            engine=explanation["engine"],
            source_movie=explanation.get("source_movie"),
            reasons=explanation.get("reasons", []),
        ),
        source=source
    )