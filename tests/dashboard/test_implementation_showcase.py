from __future__ import annotations

from dashboard.components.implementation_ideas import (
    _build_match_reveal_screens,
    _build_stats_screens,
    _build_visualization_screens,
    _compute_pair_history_snapshot,
)
from dashboard.config import CONFIG
from dashboard.services.contexts import build_pair_context


def test_showcase_builds_three_phone_concepts(alias_catalog) -> None:
    selected_demo = alias_catalog.demo_users[0]
    context = build_pair_context(
        model_key="autoencoder",
        selected_user_id=selected_demo.user_id,
        config=CONFIG,
    )

    stats_screens = _build_stats_screens(context, CONFIG)
    match_reveal_screens = _build_match_reveal_screens(context, CONFIG)
    visualization_screens = _build_visualization_screens(context, CONFIG)

    assert len(stats_screens) == 3
    assert len(match_reveal_screens) == 3
    assert len(visualization_screens) == 3
    assert all(screen.visual_html for screen in stats_screens)
    assert all(screen.visual_html for screen in match_reveal_screens)
    assert all(screen.visual_html for screen in visualization_screens)


def test_pair_history_snapshot_reads_real_listening_history(alias_catalog) -> None:
    selected_demo = alias_catalog.demo_users[0]
    context = build_pair_context(
        model_key="autoencoder",
        selected_user_id=selected_demo.user_id,
        config=CONFIG,
    )

    snapshot = _compute_pair_history_snapshot(
        selected_user_id=context.selected_user_id,
        match_user_id=context.match_user_id,
        artifact_root=str(CONFIG.paths.artifact_root),
    )

    assert snapshot is not None
    assert snapshot.selected_total_listens > 0
    assert snapshot.match_total_listens > 0
    assert snapshot.selected_minutes >= 0
    assert snapshot.match_minutes >= 0
    assert snapshot.shared_genre_name or snapshot.shared_artist_name
