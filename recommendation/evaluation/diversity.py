"""
Beyond-accuracy evaluation metrics.

Coverage  — what fraction of the catalog is ever recommended?
Diversity — how dissimilar are items within a single rec list?
Novelty   — are we recommending niche items or just popular ones?
"""

import math
from typing import Callable


def catalog_coverage(
    all_recommended: list[list[int]], catalog_size: int
) -> float:
    """
    Fraction of the catalog that appears across all recommendation
    lists.  Higher = the recommender isn't stuck in a popularity
    bubble.
    """
    if catalog_size <= 0:
        return 0.0
    unique_items: set[int] = set()
    for recs in all_recommended:
        unique_items.update(recs)
    return len(unique_items) / catalog_size


def intra_list_diversity(
    recommendations: list[int],
    similarity_fn: Callable[[int, int], float],
) -> float:
    """
    Average pairwise dissimilarity within a recommendation list.

    ``similarity_fn(a, b)`` should return a value in [0, 1].
    Diversity = 1 − mean(similarity).
    """
    n = len(recommendations)
    if n < 2:
        return 0.0

    total_dissimilarity = 0.0
    pairs = 0

    for i in range(n):
        for j in range(i + 1, n):
            sim = similarity_fn(recommendations[i], recommendations[j])
            total_dissimilarity += 1.0 - sim
            pairs += 1

    return total_dissimilarity / pairs if pairs > 0 else 0.0


def novelty(
    recommendations: list[int],
    popularity_scores: dict[int, float],
    catalog_size: int,
) -> float:
    """
    Mean self-information of recommended items.

    Novelty = mean(−log2(p_i)) where p_i = popularity / catalog_size.
    Popular items carry less information (lower novelty).
    """
    if not recommendations or catalog_size <= 0:
        return 0.0

    total = 0.0
    count = 0

    for item in recommendations:
        raw_pop = popularity_scores.get(item, 0.0)
        # Normalise to a probability
        p = raw_pop / catalog_size if catalog_size > 0 else 0.0
        if 0 < p < 1.0:
            total += -math.log2(p)
            count += 1

    return total / count if count > 0 else 0.0
