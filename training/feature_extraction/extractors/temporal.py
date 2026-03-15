import pandas as pd

from utils.logger import get_logger

logger = get_logger("feature_extraction.temporal", 20)


def peak_hour(df: pd.DataFrame, listening_history: pd.DataFrame) -> pd.DataFrame:
    """
    Generate identifier columns for whether that user spent the max amount of time
    listening to songs in that specific hour.

    TODO: Implement peak hour features based on per-user hourly distributions.
    """
    # peak_hours = user_hour_dist.idxmax(axis=1)
    return df


def night_ratio(df: pd.DataFrame, listening_history: pd.DataFrame) -> pd.DataFrame:
    """
    A ratio between the number of songs listened to between 0-5am vs. all songs listened
    to.

    TODO: This currently assumes an `hour` column already exists on listening_history.
    Derive it from `listen_timestamp` before grouping.
    """
    user_hour_dist = (
        listening_history.groupby(["user_id", "hour"]).size().unstack(fill_value=0)
    )

    night_cols = [h for h in range(6) if h in user_hour_dist.columns]
    night_counts = user_hour_dist[night_cols].sum(axis=1)
    total_counts = user_hour_dist.sum(axis=1)
    night_ratio_series = night_counts / total_counts

    df["temporal_night_ratio"] = night_ratio_series

    return df


def extract(listening_history: pd.DataFrame) -> pd.DataFrame:
    """
    Compute all temporal features for each user.

    Input:
      - listening_history: raw logs with at least user_id and hourly information

    Output:
      - dataframe indexed by user_id with temporal_* feature columns
    """
    logger.info("Extracting temporal features...")

    user_ids = listening_history["user_id"].dropna().unique()
    df = pd.DataFrame(index=user_ids)
    df.index.name = "user_id"

    return df
