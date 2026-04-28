"""Resolve listening-history path: bundle vs repo when GCS is not configured."""

from __future__ import annotations

from pathlib import Path

from dashboard.config import PathsConfig
from dashboard.services.gcs_listening import resolve_listening_history_csv_path


def _paths(tmp_path: Path) -> PathsConfig:
    root = tmp_path / "repo"
    bundle = root / "dashboard" / "artifacts"
    eds = bundle / "data" / "edgelists"
    eds.mkdir(parents=True)
    return PathsConfig(
        repo_root=root,
        artifact_root=bundle,
        dashboard_dir=root / "dashboard",
        features_path=bundle / "data" / "features_df.csv",
        full_edgelist_path=eds / "e.csv",
        experiments_dir=root / "training" / "models" / "experiments",
        training_models_dir=root / "training" / "models",
    )


def test_resolve_uses_bundle_when_csv_exists(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    target = paths.artifact_root / "data" / "past_listening_history.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("user_id;track_name\nu1;x\n", encoding="utf-8")

    got = resolve_listening_history_csv_path(paths)
    assert got == target


def test_resolve_falls_back_to_repo_data(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    legacy = paths.repo_root / "data" / "past_listening_history.csv"
    legacy.parent.mkdir(parents=True, exist_ok=True)
    legacy.write_text("user_id;track_name\nu1;x\n", encoding="utf-8")

    got = resolve_listening_history_csv_path(paths)
    assert got == legacy
