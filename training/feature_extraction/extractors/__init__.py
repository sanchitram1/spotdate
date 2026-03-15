from typing import List, Tuple

from training.feature_extraction._contract import FeatureExtractor

# from .album import extract as album_extract
from .artist import extract as artist_extract
from .audio_features import extract as audio_features_extract
from .basic import extract as basic_extract
from .genre import extract as genre_extract
from .temporal import extract as temporal_extract

ExtractorEntry = Tuple[str, FeatureExtractor]


EXTRACTORS: List[ExtractorEntry] = [
    ("basic", basic_extract),
    ("temporal", temporal_extract),
    ("genre", genre_extract),
    ("audio_features", audio_features_extract),
    # ("album", album_extract),
    ("artist", artist_extract),
]
