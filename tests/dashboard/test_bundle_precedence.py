"""Tests resolution of dashboard/artifacts bundle vs repo root data."""

from __future__ import annotations

from pathlib import Path

from dashboard.config import build_config


def test_dashboard_artifacts_take_precedence_when_populated(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    (root / "data").mkdir(parents=True)
    (root / "dashboard" / "artifacts" / "data").mkdir(parents=True)
    (root / "data" / "features_df.csv").write_text("user_id\n1\n", encoding="utf-8")
    dash_feat = root / "dashboard" / "artifacts" / "data" / "features_df.csv"
    dash_feat.write_text("user_id\n99\n", encoding="utf-8")
    eds = root / "dashboard" / "artifacts" / "data" / "edgelists"
    eds.mkdir(parents=True)
    (eds / "edgelist_dashboard_users.csv").write_text(
        "user_anchor,user_match,similarity_score\n", encoding="utf-8"
    )

    cfg = build_config(root)

    assert cfg.paths.artifact_root == root / "dashboard" / "artifacts"
    assert cfg.paths.features_path == dash_feat


def test_fallback_without_dashboard_bundle_points_at_repo(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    (root / "data").mkdir(parents=True)
    (root / "data" / "features_df.csv").write_text("user_id\n1\n", encoding="utf-8")
    eds = root / "data" / "edgelists"
    eds.mkdir(parents=True)
    (eds / "edgelist_full.csv").write_text(
        "user_anchor,user_match,similarity_score\n",
        encoding="utf-8",
    )

    cfg = build_config(root)

    assert cfg.paths.artifact_root == root
