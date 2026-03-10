import pandas as pd

from utils.logger import get_logger

logger = get_logger("feature_extraction.audio_features", 20)


def extract(listening_history: pd.DataFrame) -> pd.DataFrame:
    """
    Placeholder for advanced audio feature aggregation.

    Expected behavior for this module:
    - Input: raw listening_history with audio descriptors or embeddings.
    - Output: dataframe indexed by user_id with audio_* feature columns.
    """
    logger.info(
        "Audio feature extractor is not yet implemented; returning empty frame."
    )

    user_ids = listening_history["user_id"].dropna().unique()
    df = pd.DataFrame(index=user_ids)
    df.index.name = "user_id"

    return df

