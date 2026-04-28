"""Regression: match photos use CONFIG paths and case-insensitive file names (e.g. `.JPG`)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import dashboard.components.screen as screen_module


def test_resolve_match_image_finds_uppercase_jpg(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    matches = tmp_path / "assets" / "matches"
    matches.mkdir(parents=True)
    (matches / "winnie.JPG").write_bytes(b"\xff\xd8\xff\xe0")

    fake_config = SimpleNamespace(
        paths=SimpleNamespace(dashboard_dir=tmp_path),
    )
    monkeypatch.setattr(screen_module, "CONFIG", fake_config)
    screen_module._resolve_match_image_data_uri.cache_clear()

    uri = screen_module._resolve_match_image_data_uri("Winnie")

    assert uri.startswith("data:image/jpeg;base64,")
