"""Tests for repo-root discovery when ``dashboard`` is loaded from site-packages."""

from __future__ import annotations

from pathlib import Path

import pytest

from dashboard.config import resolve_repo_root


def test_resolve_prefers_cwd_when_bundle_lives_in_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    checkout = tmp_path / "checkout"
    (checkout / "dashboard" / "artifacts" / "data").mkdir(parents=True)
    (checkout / "dashboard" / "artifacts" / "data" / "features_df.csv").write_text(
        "user_id\n1\n", encoding="utf-8"
    )
    monkeypatch.chdir(checkout)

    fake_config = tmp_path / "venv/lib/python3.13/site-packages/dashboard/config.py"
    fake_config.parent.mkdir(parents=True)
    fake_config.write_text("#", encoding="utf-8")

    root = resolve_repo_root(config_file=fake_config, cwd=checkout)

    assert root == checkout


def test_resolve_honors_spotdate_repo_root_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    forced = tmp_path / "forced_root"
    forced.mkdir()
    monkeypatch.setenv("SPOTDATE_REPO_ROOT", str(forced))

    fake_config = tmp_path / "site-packages/dashboard/config.py"
    fake_config.parent.mkdir(parents=True)
    fake_config.write_text("#", encoding="utf-8")

    assert (
        resolve_repo_root(config_file=fake_config, cwd=tmp_path / "elsewhere") == forced
    )
