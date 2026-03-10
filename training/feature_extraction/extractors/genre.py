import pandas as pd

from utils.logger import get_logger

logger = get_logger("feature_extraction.genre", 20)


def extract(listening_history: pd.DataFrame) -> pd.DataFrame:
    """
    Placeholder for genre-based user features.

    Expected behavior for this module:
    - Input: raw listening_history with at least user_id and genre.
    - Output: dataframe indexed by user_id with genre_* feature columns
      (e.g., genre_entropy, genre_mainstream_score, etc.).
    """
    logger.info("Genre feature extractor is not yet implemented; returning empty frame.")

    user_ids = listening_history["user_id"].dropna().unique()
    df = pd.DataFrame(index=user_ids)
    df.index.name = "user_id"

    return df

