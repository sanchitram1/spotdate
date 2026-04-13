from __future__ import annotations

from dashboard.config import CONFIG
from dashboard.services.scoring import build_user_group_scores, rank_pair_groups


def test_group_scores_cover_all_semantic_groups(datasets) -> None:
    scores = build_user_group_scores(datasets.raw_features, CONFIG)

    assert set(scores.columns) == {group.key for group in CONFIG.semantic_groups}
    assert ((scores >= 0.0) & (scores <= 1.0)).all().all()


def test_pair_group_rankings_are_unique_and_sorted(datasets, alias_catalog) -> None:
    scores = build_user_group_scores(datasets.raw_features, CONFIG)
    selected, match = alias_catalog.demo_users[:2]

    ranked = rank_pair_groups(selected.user_id, match.user_id, scores, CONFIG)

    assert ranked["group_key"].is_unique
    assert ranked["pair_score"].tolist() == sorted(
        ranked["pair_score"].tolist(), reverse=True
    )
    assert len(ranked.head(CONFIG.ui.radar_axis_count)) == CONFIG.ui.radar_axis_count
