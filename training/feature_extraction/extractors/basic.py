import pandas as pd

from utils.logger import get_logger

logger = get_logger("feature_extraction.basic", 20)


def extract(listening_history: pd.DataFrame) -> pd.DataFrame:
    """
    Generates a basic user-level feature matrix from raw listening history.

    Returns a dataframe keyed by user_id with:
    - aggregate counts (tracks, artists, albums, genres)
    - average audio feature values
    - per-genre listen counts (genre_* columns)
    """
    logger.info("Extracting basic features...")

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

    # GUARD: coerce audio feature columns to numeric
    for col in audio_cols:
        listening_history[col] = pd.to_numeric(listening_history[col], errors="coerce")

    agg_funcs = {
        "track_mbid": [("total_tracks", "count"), ("n_unique_tracks", "nunique")],
        "artist_mbid": [("n_unique_artists", "nunique")],
        "album_mbid": [("n_unique_albums", "nunique")],
        "genre": [("n_unique_genres", "nunique")],
    }

    for col in audio_cols:
        agg_funcs[col] = [(f"avg_{col}", "mean")]

    basic_features = listening_history.groupby("user_id").agg(agg_funcs)
    basic_features.columns = basic_features.columns.droplevel(0)

    genre_counts = listening_history.groupby(["user_id", "genre"]).size()
    genre_features = genre_counts.unstack(level="genre", fill_value=0)
    genre_features = genre_features.add_prefix("genre_")

    final_user_features = basic_features.join(genre_features, how="left")
    final_user_features = final_user_features.fillna(0)

    return final_user_features

