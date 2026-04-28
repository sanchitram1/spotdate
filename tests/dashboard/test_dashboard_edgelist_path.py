from __future__ import annotations

from pathlib import Path

from dashboard.config import build_config


def test_config_prefers_dashboard_edgelist_when_present(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    (root / "data").mkdir(parents=True)
    (root / "data" / "features_df.csv").write_text("user_id\n0\n", encoding="utf-8")
    edgelists_dir = root / "data" / "edgelists"
    edgelists_dir.mkdir(parents=True)

    slug = root / "data" / "edgelists" / "edgelist_dashboard_users.csv"
    full = root / "data" / "edgelists" / "edgelist_full.csv"
    slug.write_text(
        "user_anchor,user_match,similarity_score\n",
        encoding="utf-8",
    )
    full.write_text(
        "user_anchor,user_match,similarity_score\n",
        encoding="utf-8",
    )

    cfg = build_config(root)

    assert cfg.paths.full_edgelist_path.resolve() == slug.resolve()


def test_config_falls_back_to_corpus_edgelist(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    (root / "data").mkdir(parents=True)
    (root / "data" / "features_df.csv").write_text("user_id\n0\n", encoding="utf-8")
    full = root / "data" / "edgelists" / "edgelist_full.csv"
    full.parent.mkdir(parents=True)
    full.write_text(
        "user_anchor,user_match,similarity_score\n",
        encoding="utf-8",
    )

    cfg = build_config(root)

    assert cfg.paths.full_edgelist_path.resolve() == full.resolve()
