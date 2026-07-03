"""
Evaluation orchestrator.

Runs all metrics against a recommender function and produces a
structured report.  Handles train/test splitting of MovieLens
ratings for offline evaluation.
"""

from typing import Callable

import pandas as pd
from pydantic import BaseModel, Field

from recommendation.evaluation.metrics import (
    precision_at_k,
    recall_at_k,
    mean_average_precision,
    ndcg_at_k,
)
from recommendation.evaluation.diversity import (
    catalog_coverage,
    intra_list_diversity,
    novelty,
)


class MetricsAtK(BaseModel):
    k: int
    precision: float
    recall: float
    ndcg: float


class EvaluationReport(BaseModel):
    """Structured output of a full evaluation run."""

    metrics_at_k: list[MetricsAtK] = Field(default_factory=list)
    map_score: float = 0.0
    coverage: float = 0.0
    avg_diversity: float = 0.0
    avg_novelty: float = 0.0
    num_users_evaluated: int = 0


class RecommenderEvaluator:
    """
    Offline evaluator for any recommender function.

    Usage::

        evaluator = RecommenderEvaluator()
        train, test = evaluator.train_test_split(ratings_df)
        report = evaluator.evaluate(my_recommender_fn, test)
        print(report.model_dump())
    """

    # ── Data splitting ─────────────────────────────────────────────

    @staticmethod
    def train_test_split(
        ratings_df: pd.DataFrame, test_fraction: float = 0.2
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Temporal split: for each user, the most recent ``test_fraction``
        of ratings go into the test set.  This is more realistic than
        random splitting because it simulates predicting future behaviour.
        """
        train_parts: list[pd.DataFrame] = []
        test_parts: list[pd.DataFrame] = []

        for _, group in ratings_df.groupby("userId"):
            sorted_group = group.sort_values("timestamp")
            split_idx = int(len(sorted_group) * (1 - test_fraction))
            train_parts.append(sorted_group.iloc[:split_idx])
            test_parts.append(sorted_group.iloc[split_idx:])

        return pd.concat(train_parts), pd.concat(test_parts)

    # ── Full evaluation ────────────────────────────────────────────

    def evaluate(
        self,
        recommender_fn: Callable[[int], list],
        test_data: pd.DataFrame,
        k_values: list[int] | None = None,
        popularity_scores: dict[int, float] | None = None,
        similarity_fn: Callable[[int, int], float] | None = None,
        catalog_size: int = 0,
        max_users: int = 50,
    ) -> EvaluationReport:
        """
        Evaluate ``recommender_fn`` against ``test_data``.

        Parameters
        ----------
        recommender_fn : Callable[[int], list]
            ``recommender_fn(user_id)`` returns a list of recommended
            item IDs (ints) or Recommendation objects with ``.tmdbId``.
        test_data : DataFrame
            Must have columns ``userId``, ``movieId``, ``rating``.
        k_values : list[int]
            Cut-off depths.  Defaults to [5, 10, 20].
        popularity_scores : dict | None
            item_id → popularity score for novelty calculation.
        similarity_fn : Callable | None
            (a, b) → similarity for diversity calculation.
        catalog_size : int
            Total items in the catalog (for coverage + novelty).
        max_users : int
            Limit number of users evaluated (for dev speed).
        """
        if k_values is None:
            k_values = [5, 10, 20]

        # ── Build ground truth ──────────────────────────────────────
        all_relevant: dict[int, set[int]] = {}
        for uid, group in test_data.groupby("userId"):
            relevant = set(
                group[group["rating"] >= 4.0]["movieId"].astype(int).tolist()
            )
            if relevant:
                all_relevant[int(uid)] = relevant

        if not all_relevant:
            return EvaluationReport()

        # ── Generate recommendations ────────────────────────────────
        users_to_eval = list(all_relevant.keys())[:max_users]
        all_recommended: dict[int, list[int]] = {}
        all_rec_lists: list[list[int]] = []
        max_k = max(k_values)

        for uid in users_to_eval:
            try:
                recs = recommender_fn(uid)
                # Handle both int lists and Recommendation objects
                rec_ids = [
                    r if isinstance(r, int) else getattr(r, "tmdbId", r)
                    for r in recs
                ]
                rec_ids = [r for r in rec_ids if r is not None]
                all_recommended[uid] = rec_ids[:max_k]
                all_rec_lists.append(rec_ids[:max_k])
            except Exception:
                continue

        if not all_recommended:
            return EvaluationReport()

        # ── Accuracy metrics at each K ──────────────────────────────
        metrics_at_k: list[MetricsAtK] = []
        for k in k_values:
            precisions, recalls, ndcgs = [], [], []

            for uid in all_recommended:
                if uid not in all_relevant:
                    continue
                recs = all_recommended[uid]
                rel = all_relevant[uid]
                precisions.append(precision_at_k(recs, rel, k))
                recalls.append(recall_at_k(recs, rel, k))
                ndcgs.append(ndcg_at_k(recs, rel, k))

            metrics_at_k.append(
                MetricsAtK(
                    k=k,
                    precision=(
                        sum(precisions) / len(precisions)
                        if precisions
                        else 0.0
                    ),
                    recall=(
                        sum(recalls) / len(recalls) if recalls else 0.0
                    ),
                    ndcg=sum(ndcgs) / len(ndcgs) if ndcgs else 0.0,
                )
            )

        # ── MAP ─────────────────────────────────────────────────────
        map_val = mean_average_precision(all_recommended, all_relevant)

        # ── Coverage ────────────────────────────────────────────────
        cov = (
            catalog_coverage(all_rec_lists, catalog_size)
            if catalog_size > 0
            else 0.0
        )

        # ── Diversity ───────────────────────────────────────────────
        avg_div = 0.0
        if similarity_fn:
            diversities = [
                intra_list_diversity(recs, similarity_fn)
                for recs in all_rec_lists
                if len(recs) >= 2
            ]
            avg_div = (
                sum(diversities) / len(diversities) if diversities else 0.0
            )

        # ── Novelty ─────────────────────────────────────────────────
        avg_nov = 0.0
        if popularity_scores and catalog_size > 0:
            novelties = [
                novelty(recs, popularity_scores, catalog_size)
                for recs in all_rec_lists
            ]
            avg_nov = (
                sum(novelties) / len(novelties) if novelties else 0.0
            )

        return EvaluationReport(
            metrics_at_k=metrics_at_k,
            map_score=map_val,
            coverage=cov,
            avg_diversity=avg_div,
            avg_novelty=avg_nov,
            num_users_evaluated=len(all_recommended),
        )
