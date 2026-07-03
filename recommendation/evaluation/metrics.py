"""
Information-retrieval evaluation metrics.

All functions follow the same convention:
    recommended : list[int]   — ordered list of item IDs (best first)
    relevant    : set[int]    — ground-truth set of relevant item IDs
    k           : int         — cut-off depth

Scores are always in [0, 1].
"""

import math


def precision_at_k(
    recommended: list[int], relevant: set[int], k: int
) -> float:
    """Fraction of top-K items that are relevant."""
    if k <= 0:
        return 0.0
    top_k = recommended[:k]
    if not top_k:
        return 0.0
    return sum(1 for item in top_k if item in relevant) / len(top_k)


def recall_at_k(
    recommended: list[int], relevant: set[int], k: int
) -> float:
    """Fraction of relevant items that appear in top-K."""
    if not relevant or k <= 0:
        return 0.0
    top_k = recommended[:k]
    return sum(1 for item in top_k if item in relevant) / len(relevant)


def average_precision(
    recommended: list[int], relevant: set[int]
) -> float:
    """
    Average Precision for a single query/user.

    AP = (1/|relevant|) * sum_{k where rec_k is relevant}( P@k )
    """
    if not relevant:
        return 0.0
    score = 0.0
    hits = 0
    for i, item in enumerate(recommended):
        if item in relevant:
            hits += 1
            score += hits / (i + 1)
    return score / len(relevant)


def mean_average_precision(
    all_recommended: dict[int, list[int]],
    all_relevant: dict[int, set[int]],
) -> float:
    """MAP across multiple users."""
    if not all_recommended:
        return 0.0
    total, count = 0.0, 0
    for uid in all_recommended:
        if uid in all_relevant:
            total += average_precision(
                all_recommended[uid], all_relevant[uid]
            )
            count += 1
    return total / count if count > 0 else 0.0


def dcg_at_k(
    recommended: list[int], relevant: set[int], k: int
) -> float:
    """Discounted Cumulative Gain at K (binary relevance)."""
    score = 0.0
    for i, item in enumerate(recommended[:k]):
        if item in relevant:
            score += 1.0 / math.log2(i + 2)  # +2 because log2(1)=0
    return score


def idcg_at_k(relevant: set[int], k: int) -> float:
    """Ideal DCG — best possible DCG with |relevant| hits in top-K."""
    n = min(len(relevant), k)
    return sum(1.0 / math.log2(i + 2) for i in range(n))


def ndcg_at_k(
    recommended: list[int], relevant: set[int], k: int
) -> float:
    """Normalized DCG at K."""
    ideal = idcg_at_k(relevant, k)
    if ideal == 0:
        return 0.0
    return dcg_at_k(recommended, relevant, k) / ideal
