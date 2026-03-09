#!/usr/bin/env pkgx uv run

import argparse

import pandas as pd

from utils.logger import get_logger

# Hyperparameters / defaults
POPULARITY_FILL = 50
TIME_QUANTILE = 0.8
TOP_K = 7

logger = get_logger("label_generation", 20)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a user-user edgelist (labels) from a listening history CSV."
        ),
    )
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Path to the input listening history CSV file.",
    )
    parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Directory where edgelist.csv will be written.",
    )
    return parser.parse_args()


def generate_edgelist(listening_history: pd.DataFrame) -> pd.DataFrame:
    """Generate a user-user edgelist based on future listening history.

    The actual matching logic (e.g. hipster overlap) is delegated to a separate
    function so we can easily swap in alternative matching strategies later.
    """
    logger.info("Starting edgelist generation...")

    # Ensure popularity is numeric and fill missing
    listening_history["popularity"] = pd.to_numeric(
        listening_history["popularity"], errors="coerce"
    ).fillna(POPULARITY_FILL)

    # Parse timestamps in a robust way so we can split on time
    listening_history["listen_timestamp"] = pd.to_datetime(
        listening_history["listen_timestamp"], errors="coerce", utc=True
    )

    # Drop rows where timestamp could not be parsed
    before_drop = len(listening_history)
    listening_history = listening_history.dropna(subset=["listen_timestamp"])
    after_drop = len(listening_history)
    if after_drop < before_drop:
        logger.warning(
            "Dropped %d rows with invalid listen_timestamp.", before_drop - after_drop
        )

    # Time-based split: past vs future
    cutoff_date = listening_history["listen_timestamp"].quantile(TIME_QUANTILE)
    logger.info("Computed cutoff date at quantile %.2f: %s", TIME_QUANTILE, cutoff_date)

    past_df = listening_history[listening_history["listen_timestamp"] <= cutoff_date]
    future_df = listening_history[listening_history["listen_timestamp"] > cutoff_date]

    logger.info(
        "Split into past (%d rows) and future (%d rows).",
        len(past_df),
        len(future_df),
    )

    # Delegate to a specific matching strategy (hipster overlap for now)
    edge_list = hipster_overlap_edges(future_df=future_df, top_k=TOP_K)

    logger.info(
        "Generated edge list with %d rows and %d unique anchor users.",
        len(edge_list),
        edge_list["user_id_anchor"].nunique(),
    )

    return edge_list


def hipster_overlap_edges(future_df: pd.DataFrame, top_k: int) -> pd.DataFrame:
    """Compute user-user edges using the 'hipster overlap' scoring."""
    # Unique user-track combos in the future to avoid over-counting loops
    future_tracks = future_df[["user_id", "track_mbid", "popularity"]].drop_duplicates()

    # Hipster weight: inverse popularity
    future_tracks["hipster_weight"] = 100 - future_tracks["popularity"]

    # Self-merge on track_mbid to find users who listened to the same tracks
    overlaps = pd.merge(
        future_tracks[["user_id", "track_mbid", "hipster_weight"]],
        future_tracks[["user_id", "track_mbid"]],
        on="track_mbid",
        suffixes=("_anchor", "_positive"),
    )

    # Remove self-matches and duplicate (symmetric) pairs
    overlaps = overlaps[overlaps["user_id_anchor"] < overlaps["user_id_positive"]]

    # Sum hipster weights for each unique user pair
    pair_scores = (
        overlaps.groupby(["user_id_anchor", "user_id_positive"])["hipster_weight"]
        .sum()
        .reset_index()
    )
    pair_scores.rename(columns={"hipster_weight": "match_score"}, inplace=True)

    # For each anchor user, keep Top K matches by score
    pair_scores = pair_scores.sort_values(
        ["user_id_anchor", "match_score"], ascending=[True, False]
    )
    edge_list = pair_scores.groupby("user_id_anchor").head(top_k).reset_index(
        drop=True
    )

    return edge_list


def main() -> None:
    args = parse_args()
    input_path = args.input
    output_dir = args.output

    logger.info("Reading listening history from %s", input_path)
    listening_history = pd.read_csv(input_path, delimiter=";")

    edge_list = generate_edgelist(listening_history=listening_history)

    output_path = f"{output_dir}/edgelist.csv"
    logger.info("Writing edge list to %s", output_path)
    edge_list.to_csv(
        output_path,
        columns=["user_id_anchor", "user_id_positive", "match_score"],
        index=False,
    )
    logger.info("Done.")


if __name__ == "__main__":
    main()

