import pandas as pd

from utils.logger import get_logger

logger = get_logger("feature_extraction.artist", 20)


def extract(listening_history: pd.DataFrame) -> pd.DataFrame:
    """
    Placeholder for artist-level user features.

    Expected behavior for this module:
    - Input: raw listening_history with artist_mbid or artist identifiers.
    - Output: dataframe indexed by user_id with artist_* feature columns.
    """
    logger.info(
        "Artist feature extractor is not yet implemented; returning empty frame."
    )

    user_ids = listening_history["user_id"].dropna().unique()
    df = pd.DataFrame(index=user_ids)
    df.index.name = "user_id"

    return df

