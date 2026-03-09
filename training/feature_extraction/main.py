import argparse

import pandas as pd

from utils.logger import get_logger

logger = get_logger("feature_extraction", 20)
# OUTPUT_PATH = "../../data"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Take an input listening history and return a feature enriched dataset"
        ),
    )
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Path to the input CSV file.",
    )
    parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Path to the output CSV file.",
    )
    return parser.parse_args()


def basic(listening_history: pd.DataFrame) -> pd.DataFrame:
    """
    Generates a basic user-level feature matrix from raw listening history.
    """
    logger.info("Extracting basic features...")

    # audio features I'll average
    audio_cols = [
        "acousticness",
        "danceability",
        "energy",
        "instrumentalness",
        "liveness",
        "loudness",
        "speechiness",
        "tempo",
        "valence",
    ]

    # GUARD
    for col in audio_cols:
        listening_history[col] = pd.to_numeric(listening_history[col], errors="coerce")

    # 1. aggregation
    agg_funcs = {
        "track_mbid": [("total_tracks", "count"), ("n_unique_tracks", "nunique")],
        "artist_mbid": [("n_unique_artists", "nunique")],
        "album_mbid": [("n_unique_albums", "nunique")],
        "genre": [("n_unique_genres", "nunique")],
    }

    # average of each audio feature
    for col in audio_cols:
        agg_funcs[col] = [(f"avg_{col}", "mean")]

    # aggregate
    basic_features = listening_history.groupby("user_id").agg(agg_funcs)

    # weird return, needs this instead of ...reset_index()
    basic_features.columns = basic_features.columns.droplevel(0)

    # 2. counts of each genre
    logger.info("Calculating genre distributions...")

    genre_counts = listening_history.groupby(["user_id", "genre"]).size()
    genre_features = genre_counts.unstack(level="genre", fill_value=0)
    genre_features = genre_features.add_prefix("genre_")

    # 3. merge
    final_user_features = basic_features.join(genre_features, how="left")
    final_user_features = final_user_features.fillna(0)

    return final_user_features


def main():
    # parse
    args = parse_args()
    input = args.input
    output = args.output

    # pipeline
    listening_history = pd.read_csv(input, delimiter=";")
    user_df = basic(listening_history=listening_history)
    user_df.to_csv(f"{output}/features_df.csv")


if __name__ == "__main__":
    main()
