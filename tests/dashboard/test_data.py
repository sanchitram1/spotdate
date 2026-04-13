from __future__ import annotations

from dashboard.config import CONFIG
from dashboard.services.data import detect_delimiter, preprocess_features


def test_detect_delimiter_matches_saved_artifacts() -> None:
    assert detect_delimiter(CONFIG.paths.features_path) == ","
    assert detect_delimiter(CONFIG.paths.full_edgelist_path) == ","


def test_preprocess_features_matches_notebook_contract(datasets) -> None:
    model_matrix = preprocess_features(datasets.raw_features.reset_index(drop=True))

    assert model_matrix.shape[0] == datasets.raw_features.shape[0]
    assert model_matrix.index.tolist() == datasets.raw_features["user_id"].tolist()
    assert "user_type_loyal_Follower/Others" in model_matrix.columns
    assert "user_id" not in model_matrix.columns
    assert not model_matrix.isna().any().any()
