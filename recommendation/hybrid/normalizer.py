from recommendation.common.schemas import Recommendation


def min_max_normalize(values: list[float]) -> list[float]:
    """
    Min-Max normalize a list of values to the range [0, 1].

    If all values are identical, returns 1.0 for every value.
    """

    if not values:
        return []

    minimum = min(values)
    maximum = max(values)

    if minimum == maximum:
        return [1.0] * len(values)

    return [
        (value - minimum) / (maximum - minimum)
        for value in values
    ]


def normalize_scores(
    recommendations: list[Recommendation],
    score_type: str,
) -> dict[int, float]:
    """
    Normalize one score field across all recommendations.

    Parameters
    ----------
    recommendations : list[Recommendation]

    score_type : str
        One of:
            "content"
            "collaborative"
            "popularity"

    Returns
    -------
    dict[int, float]

    Example:
    {
        27205: 0.93,
        157336: 0.88,
        603: 0.74
    }
    """

    scores = []
    movie_ids = []

    for movie in recommendations:

        value = getattr(movie.scores, score_type)

        if value is None:
            continue

        scores.append(value)
        movie_ids.append(movie.tmdbId)

    normalized = min_max_normalize(scores)

    return dict(zip(movie_ids, normalized))