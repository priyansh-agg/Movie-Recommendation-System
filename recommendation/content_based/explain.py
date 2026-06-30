from recommendation.content_based.loader import movie_metadata

import ast
def convert(text):
    return text.split()

movie_metadata["genres"] = movie_metadata["genres"].apply(convert)
movie_metadata["keywords"] = movie_metadata["keywords"].apply(convert)
movie_metadata["cast"] = movie_metadata["cast"].apply(convert)


def _shared_genres(movie1, movie2):
    return list(set(movie1["genres"]) & set(movie2["genres"]))


def _shared_keywords(movie1, movie2):
    return list(set(movie1["keywords"]) & set(movie2["keywords"]))


def _shared_cast(movie1, movie2):
    return list(set(movie1["cast"]) & set(movie2["cast"]))


def _same_director(movie1, movie2):
    if (
        movie1["crew"] != "" and
        movie1["crew"] == movie2["crew"]
    ):
        return movie1["crew"]

    return None


def generate_explanation(
    source_index,
    recommended_index,
    similarity_score
):

    liked_movie = movie_metadata.iloc[
        source_index    
    ]

    recommended_movie = movie_metadata.iloc[
        recommended_index
    ]

    reasons = []

    genres = _shared_genres(
        liked_movie,
        recommended_movie
    )

    if genres:
        reasons.append(
            "Shared genres: " +
            ", ".join(genres[:3])
        )

    keywords = _shared_keywords(
        liked_movie,
        recommended_movie
    )

    if keywords:
        reasons.append(
            "Common themes: " +
            ", ".join(keywords[:3])
        )

    cast = _shared_cast(
        liked_movie,
        recommended_movie
    )

    if cast:
        reasons.append(
            "Featuring " +
            ", ".join(cast[:2])
        )

    director = _same_director(
        liked_movie,
        recommended_movie
    )

    if director:
        reasons.append(
            f"Directed by {director}"
        )

    reasons.append(
        f"Similarity Score: {similarity_score:.0%}"
    )

    return reasons