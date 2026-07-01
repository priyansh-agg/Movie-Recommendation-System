import pickle

from recommendation.collaborative.loader import load_movies, load_ratings
from recommendation.mapping.loader import resolve_movie
from recommendation.common.builder import build_recommendation

model = pickle.load(
    open("recommendation/collaborative/models/svd_model.pkl", "rb")
)
movies = load_movies()
ratings = load_ratings()


def recommend(user_id, top_n=10):
    """
    Generate collaborative filtering recommendations for a user.

    Uses the pre-trained SVD model to predict ratings for every unseen
    movie, then returns the top-N with the highest predicted rating.

    Args:
        user_id: MovieLens user ID.
        top_n: Number of recommendations to return.

    Returns:
        list[Recommendation]: Ranked collaborative recommendations.
    """

    watched = set(ratings[ratings.userId == user_id]["movieId"])

    # ── Stage 1: Predict ratings for every unseen movie ─────────────
    predictions = []
    for mid in movies.movieId:
        if mid in watched:
            continue
        pred = model.predict(user_id, mid)
        predictions.append((mid, pred.est))

    if not predictions:
        return []

    # Sort once AFTER all predictions are collected.
    predictions.sort(key=lambda x: x[1], reverse=True)

    # ── Stage 2: Build Recommendation objects for top candidates ────
    recommendations = []
    for mid, predicted_rating in predictions:
        if len(recommendations) >= top_n:
            break

        movie = resolve_movie(mid)
        if movie is None:
            continue

        recommendations.append(
            build_recommendation(
                movie_id=movie["movieId"],
                tmdb_id=movie["tmdbId"],
                title=movie["title"],
                poster=movie["poster"],
                metadata=movie["metadata"],
                explanation={
                    "engine": "collaborative",
                    "source_movie": None,
                    "reasons": [
                        "Users with similar taste highly rated this movie.",
                        f"Predicted rating: {predicted_rating:.1f}/5.0",
                    ],
                },
                collaborative_score=float(predicted_rating),
                source="collaborative",
            )
        )

    return recommendations
