import numpy as np
from recommendation.content_based.loader import (
    similarity,rating,movie_titles,movie_to_index
)
from recommendation.services.poster_service import fetch_poster
from recommendation.content_based.explain import generate_explanation

def recommend(movie_list,top_n=5):
    """
    Recommend movies based on one or more input movies.

    Args:
        movie_list (list[str]): List of movie titles liked by the user.
        top_n (int): Number of recommendations.

    Returns:
        list[dict]: Recommended movies.
    """

    indices = [movie_to_index[movie] for movie in movie_list if movie in movie_to_index]

    if not indices: 
        return []
    
    avg_similarity = np.mean(similarity[indices],axis=0)

    candidates = [
        (idx, score)
        for idx, score in enumerate(avg_similarity)
        if score > 0.25
    ]
    ranked = []
    for idx, sim_score in candidates:
        final_score = (
            0.86 * sim_score +
            0.08 * rating[idx][0] +
            0.06 * rating[idx][1]
        )

        best_source = max(
            indices,
            key=lambda liked_idx: similarity[liked_idx][idx]
        )

        ranked.append((idx, final_score, sim_score,best_source))
        ranked.sort(key=lambda x: x[1], reverse=True)

    recommendations = []
    for idx, final_score, similarity_score,best_source in ranked:
        if idx in indices:
            continue

        explanation = generate_explanation(best_source,idx,similarity_score)

        recommendations.append({
        "id": int(movie_titles.iloc[idx].id),
        "title": movie_titles.iloc[idx].title,
        "poster": fetch_poster(movie_titles.iloc[idx].id),
        "similarity": float(similarity_score),
        "score": float(final_score),
        "source_movie": movie_titles.iloc[best_source].title,
        "explanation": explanation
    })

        if len(recommendations) == top_n:
            break

    return recommendations