from __future__ import annotations

from dashboard.config import CONFIG
from dashboard.services.data import (
    _future_alignment_via_chunks_streaming,
    detect_delimiter,
    preprocess_features,
)


def test_detect_delimiter_matches_saved_artifacts() -> None:
    assert detect_delimiter(CONFIG.paths.features_path) == ","
    assert detect_delimiter(CONFIG.paths.full_edgelist_path) == ","


def test_future_alignment_chunk_scan_filters_to_anchor_and_matches(
    tmp_path,
) -> None:
    path = tmp_path / "edgelist.csv"
    path.write_text(
        "user_anchor,user_match,similarity_score\n"
        "anchor_a,match_1,0.88\n"
        "anchor_a,match_2,0.12\n"
        "other,x,0.99\n",
        encoding="utf-8",
    )
    out = _future_alignment_via_chunks_streaming(
        path,
        "anchor_a",
        frozenset({"match_1", "match_2"}),
    )
    assert out[("anchor_a", "match_1")] == 0.88
    assert out[("anchor_a", "match_2")] == 0.12
    assert ("other", "x") not in out


def test_preprocess_features_matches_notebook_contract(datasets) -> None:
    model_matrix = preprocess_features(datasets.raw_features.reset_index(drop=True))

    assert model_matrix.shape[0] == datasets.raw_features.shape[0]
    assert model_matrix.index.tolist() == datasets.raw_features["user_id"].tolist()
    assert "user_type_loyal_Follower/Others" in model_matrix.columns
    assert "user_id" not in model_matrix.columns
    assert not model_matrix.isna().any().any()
