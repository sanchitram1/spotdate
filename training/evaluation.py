from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from utils.logger import get_logger

logger = get_logger("evaluation")


@dataclass
class RecommenderConfig:
    k: int = 20
    high_score: float = 0.99
    top_percentile: float = 0.95  # top 5 percent of matches


config = RecommenderConfig()


class RecommenderEvaluator:
    """
    Stateful evaluator for recommendation models.
    Computes similarities once to save memory and compute time.
    """

    def __init__(
        self,
        embeddings: np.ndarray,
        user_ids: np.ndarray,
        full_edgelist: pd.DataFrame,
    ):
        self.k = config.k
        self.user_ids = np.array(user_ids)
        self.full_edgelist = full_edgelist

        logger.debug("1/2: Computing similarity matrix and model predictions...")
        self.model_predictions = self._get_model_predictions(embeddings)

        logger.debug("2/2: Pre-building Ground Truth Maps...")
        self.gt_top_k = self._build_gt_top_k()
        self.gt_high_score = self._build_gt_high_score(threshold=config.high_score)
        self.gt_top_5_percent = self._build_gt_percentile(
            percentile=config.top_percentile
        )

        logger.info("Evaluator ready!")

    def _get_model_predictions(self, embeddings) -> dict[str, set]:
        """Calculates cosine similarity and extracts Top K matches for each user."""
        sim_matrix = cosine_similarity(embeddings)

        # set the diagonal to negative infinity so a user is never matched with itself
        np.fill_diagonal(sim_matrix, -np.inf)

        preds = {}
        for idx, user_id in enumerate(self.user_ids):
            user_sims = sim_matrix[idx]

            # grab indices of top K
            top_indices = np.argpartition(user_sims, -self.k)[-self.k :]

            # convert indices to user IDs and store as a set
            preds[user_id] = set(self.user_ids[top_indices])

        return preds

    # TODO: this is kind of repeated. I should save these and I/O read them once?
    # or build in notebook
    def _build_gt_top_k(self) -> dict[str, set]:
        """Builds a map of the actual top K matches per user based on edgelist score."""
        sorted_df = self.full_edgelist.sort_values(
            ["user_anchor", "similarity_score"], ascending=[True, False]
        )
        top_k_df = sorted_df.groupby("user_anchor").head(self.k)
        return top_k_df.groupby("user_anchor")["user_match"].apply(set).to_dict()

    def _build_gt_high_score(self, threshold: float) -> dict[str, set]:
        """Builds a map of matches that score above a strict threshold."""
        high_score_df = self.full_edgelist[
            self.full_edgelist["similarity_score"] >= threshold
        ]
        return high_score_df.groupby("user_anchor")["user_match"].apply(set).to_dict()

    def _build_gt_percentile(self, percentile: float) -> dict[str, set]:
        """Builds a map of matches that fall into the top X% FOR THAT SPECIFIC USER."""
        # Calculate the threshold dynamically for each user
        thresholds = self.full_edgelist.groupby("user_anchor")[
            "similarity_score"
        ].transform(lambda x: x.quantile(percentile))
        perc_df = self.full_edgelist[
            self.full_edgelist["similarity_score"] >= thresholds
        ]
        return perc_df.groupby("user_anchor")["user_match"].apply(set).to_dict()

    # METRICS

    def hit_rate_at_k(self) -> float:
        """Does at least 1 prediction appear in the true Top K?"""
        hits = 0
        valid_users = 0

        for user, preds in self.model_predictions.items():
            true_top_k = self.gt_top_k.get(user)
            if not true_top_k:
                continue

            # If the intersection is not empty, it's a hit!
            if preds & true_top_k:
                hits += 1
            valid_users += 1

        return hits / valid_users if valid_users > 0 else 0.0

    def precision_at_high_score(self) -> float:
        """Precision: Out of the K items we suggested, how many were > {config.high_score} score?"""
        total_precision = 0
        valid_users = 0

        for user, preds in self.model_predictions.items():
            true_high_scores = self.gt_high_score.get(user, set())

            # Intersection size / K
            user_precision = len(preds & true_high_scores) / self.k
            total_precision += user_precision
            valid_users += 1

        return total_precision / valid_users if valid_users > 0 else 0.0

    def recall_at_top_percentile(self) -> float:
        """Recall @ Top 5%: How many of the user's elite 5% matches did we find?"""
        total_recall = 0
        valid_users = 0

        for user, preds in self.model_predictions.items():
            true_top_perc = self.gt_top_5_percent.get(user)
            if not true_top_perc:
                continue

            user_recall = len(preds & true_top_perc) / len(true_top_perc)
            total_recall += user_recall
            valid_users += 1

        return total_recall / valid_users if valid_users > 0 else 0.0

    def omission_count(self) -> float:
        """Omission Count: Average number of 'misses' per user (K - successful matches in Top K)."""
        total_omissions = 0
        valid_users = 0

        for user, preds in self.model_predictions.items():
            true_top_k = self.gt_top_k.get(user)
            if not true_top_k:
                continue

            successful_matches = len(preds & true_top_k)
            total_omissions += self.k - successful_matches
            valid_users += 1

        return total_omissions / valid_users if valid_users > 0 else 0.0

    def get_all_metrics(self) -> dict[str, float]:
        """Convenience method to run everything at once."""
        return {
            "hit_rate_at_k": self.hit_rate_at_k(),
            "precision_at_high_score": self.precision_at_high_score(),
            "recall_at_top_5_percent": self.recall_at_top_percentile(),
            "omission_count": self.omission_count(),
        }
