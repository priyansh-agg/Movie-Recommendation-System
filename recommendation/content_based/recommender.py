"""
Content-based recommender.

Supports both dense and sparse similarity matrices (auto-detected
by the loader).
"""

import numpy as np

from recommendation.content_based.loader import (
    similarity,
    similarity_sparse,
    SIMILARITY_MODE,
    rating,
    movie_titles,
    movie_to_index,
    metadata_lookup,
)
from recommendation.services.poster_service import fetch_poster
from recommendation.content_based.explain import generate_explanation
from recommendation.common.builder import build_recommendation


def _get_similar_scores_sparse(indices, n_movies):
    """
    Build an average similarity vector from sparse top-K neighbours.

    For each input movie index, look up its top-K neighbours and
    accumulate scores.  Movies not in any neighbour list get 0.
    """
    scores = np.zeros(n_movies, dtype=np.float32)
    counts = np.zeros(n_movies, dtype=np.float32)

    for idx in indices:
        neighbours = similarity_sparse.get(idx, [])
        for neighbour_idx, sim_score in neighbours:
            scores[neighbour_idx] += sim_score
            counts[neighbour_idx] += 1

    # Average where we have data
    mask = counts > 0
    scores[mask] /= counts[mask]
    return scores


def _get_pairwise_score_sparse(liked_idx, target_idx):
    """Look up similarity between two movies from sparse data."""
    neighbours = similarity_sparse.get(liked_idx, [])
    for nidx, score in neighbours:
        if nidx == target_idx:
            return score
    return 0.0


def recommend(movie_list, top_n=5):
    """
    Recommend movies based on one or more input movies.

    Args:
        movie_list (list[str]): List of movie titles liked by the user.
        top_n (int): Number of recommendations.

    Returns:
        list[Recommendation]: Recommended movies.
    """
    indices = [
        movie_to_index[movie]
        for movie in movie_list
        if movie in movie_to_index
    ]

    if not indices:
        return []

    n_movies = len(movie_titles)

    # ── Compute similarity scores ───────────────────────────────────
    if SIMILARITY_MODE == "sparse":
        avg_similarity = _get_similar_scores_sparse(indices, n_movies)
    else:
        avg_similarity = np.mean(similarity[indices], axis=0)

    # ── Filter candidates above threshold ───────────────────────────
    candidates = [
        (idx, score)
        for idx, score in enumerate(avg_similarity)
        if score > 0.25
    ]

    # ── Rank by weighted score ──────────────────────────────────────
    ranked = []
    for idx, sim_score in candidates:
        final_score = (
            0.86 * sim_score
            + 0.08 * rating[idx][0]
            + 0.06 * rating[idx][1]
        )

        # Find which liked movie is most similar to this candidate
        if SIMILARITY_MODE == "sparse":
            best_source = max(
                indices,
                key=lambda liked_idx: _get_pairwise_score_sparse(
                    liked_idx, idx
                ),
            )
        else:
            best_source = max(
                indices,
                key=lambda liked_idx: similarity[liked_idx][idx],
            )

        ranked.append((idx, final_score, sim_score, best_source))

    ranked.sort(key=lambda x: x[1], reverse=True)

    # ── Build recommendation objects ────────────────────────────────
    recommendations = []
    for idx, final_score, similarity_score, best_source in ranked:
        if idx in indices:
            continue

        explanation = generate_explanation(
            best_source, idx, similarity_score
        )

        tmdb_id = int(movie_titles.iloc[idx].id)
        metadata = metadata_lookup.get(tmdb_id)

        recommendations.append(
            build_recommendation(
                tmdb_id=tmdb_id,
                title=movie_titles.iloc[idx].title,
                poster=fetch_poster(tmdb_id),
                metadata=metadata,
                explanation={
                    "engine": "content",
                    "source_movie": movie_titles.iloc[best_source].title,
                    "reasons": explanation,
                },
                content_score=float(similarity_score),
                popularity_score=float(rating[idx][1]),
                source="content",
            )
        )

        if len(recommendations) == top_n:
            break

    return recommendations