import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from evaluation import RecommenderEvaluator, config

from utils.logger import get_logger

logger = get_logger("plotter")


def plot_score_distribution(
    evaluator: RecommenderEvaluator, model_name="Current Model"
):
    """
    Plots a histogram of the ground truth similarity scores
    for the model's Top-K recommendations.
    """
    # 1. Collect all scores
    score_lookup = evaluator.full_edgelist.set_index(["user_anchor", "user_match"])[
        "similarity_score"
    ].to_dict()
    found_scores = []

    for anchor, preds in evaluator.model_predictions.items():
        for match in preds:
            score = score_lookup.get((anchor, match))
            if score is not None:
                found_scores.append(score)

    # 2. Plotting
    plt.figure(figsize=(10, 6))
    sns.histplot(found_scores, bins=50, kde=True, color="teal")

    # Add a vertical line for your Precision threshold (0.99)
    plt.axvline(
        config.high_score,
        color="red",
        linestyle="--",
        label=f"Precision Threshold ({config.high_score})",
    )

    plt.title(
        f"Distribution of Ground Truth Scores for {model_name} Top-{evaluator.k} Picks"
    )
    plt.xlabel("Ground Truth Similarity Score")
    plt.ylabel("Frequency")
    plt.legend()
    plt.grid(axis="y", alpha=0.3)
    plt.show()

    logger.info("Median Score: %.4f", np.median(found_scores))
