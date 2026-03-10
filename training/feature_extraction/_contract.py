from typing import Protocol, runtime_checkable

import pandas as pd

EXPECTED_COLUMNS = [
    "user_id",
    "listen_timestamp",
    "track_mbid",
    "track_name",
    "artist_mbid",
    "album_mbid",
    "genre",
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


@runtime_checkable
class FeatureExtractor(Protocol):
    def __call__(self, listening_history: pd.DataFrame) -> pd.DataFrame: ...


def ensure_user_index(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure that the dataframe is indexed by user_id.

    Accepts either:
    - a dataframe with a user_id column, or
    - a dataframe whose index is already named user_id.
    """
    if df.index.name == "user_id":
        return df

    if "user_id" in df.columns:
        df = df.set_index("user_id", drop=True)
        return df

    raise ValueError("Feature extractor output must be keyed by `user_id`.")
