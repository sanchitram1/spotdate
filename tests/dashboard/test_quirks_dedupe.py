from __future__ import annotations

from pathlib import Path

import pandas as pd

from dashboard.components.implementation_ideas import (
    _common_chords_heading,
    _first_selected_quirk_not_duplicate_display,
)
from dashboard.config import CONFIG
from dashboard.ideas.quirks import QuirkDisplayItem, QuirksIdea
from dashboard.types import DemoUserOption, ModelArtifactSpec, PairContext


def _minimal_pair_context(
    tmp_path: Path,
    group_rankings: pd.DataFrame,
) -> PairContext:
    manifest = tmp_path / "manifest.csv"
    model = tmp_path / "m.pt"
    manifest.write_text("x\n0\n", encoding="utf-8")
    model.write_bytes(b"")

    spec = ModelArtifactSpec(
        key="siamese",
        label="S",
        manifest_path=manifest,
        model_path=model,
        selection_metric="x",
        selection_value=0.0,
        metadata={},
    )
    dummy = DemoUserOption(
        key="k",
        alias="Me",
        user_id="u1",
        blurb="",
    )
    prof = pd.Series(dtype=float)
    empty = pd.DataFrame()

    return PairContext(
        model_key="siamese",
        model_label="S",
        model_spec=spec,
        demo_user=dummy,
        selected_user_id="u1",
        selected_alias="Me",
        selected_profile=prof,
        match_user_id="u2",
        match_alias="Them",
        match_profile=prof,
        predicted_similarity=0.5,
        future_alignment_score=0.5,
        top_matches=empty,
        projection=empty,
        group_rankings=group_rankings,
    )


def test_green_and_quirk_exclude_same_semantic_item_key_after_build(
    tmp_path: Path,
) -> None:
    """Green row + same-dimension quirk row used to leave both ``Energy`` items."""
    group_rankings = pd.DataFrame(
        [
            {"label": "Energy", "selected_score": 0.9, "match_score": 0.9},
            {"label": "Energy", "selected_score": 0.9, "match_score": 0.5},
        ]
    )
    ctx = _minimal_pair_context(tmp_path, group_rankings)
    payload = QuirksIdea().build(ctx, CONFIG)

    gf_keys = {x.key for x in payload.green_flag_items}
    quirk_keys = {x.key for x in payload.selected_quirk_items}
    assert gf_keys.isdisjoint(quirk_keys)


def test_visible_heading_skips_collision_tempo_mapped_to_fast() -> None:
    flag = QuirkDisplayItem(key="Tempo", text="same")
    collide = QuirkDisplayItem(key="Tempo", text="oops")
    other = QuirkDisplayItem(key="Mood", text="fine")
    assert _common_chords_heading("Tempo") == "Fast"
    picked = _first_selected_quirk_not_duplicate_display(
        flag,
        [collide, other],
    )
    assert picked is not None
    assert picked.key == "Mood"


def test_visible_heading_only_collides_then_none() -> None:
    flag = QuirkDisplayItem(key="Tempo", text="a")
    only = QuirkDisplayItem(key="Tempo", text="b")
    assert _first_selected_quirk_not_duplicate_display(flag, [only]) is None
