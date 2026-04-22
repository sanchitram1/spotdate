from __future__ import annotations

from dashboard.config import CONFIG
from dashboard.services.contexts import build_pair_context, load_alias_catalog
from dashboard.services.overview import (
    build_model_comparison_rows,
    build_runtime_health_rows,
    build_runtime_summary,
)


def test_runtime_summary_uses_demo_context_cleanly() -> None:
    demo_catalog = load_alias_catalog(demo_mode=True)
    selected_demo = demo_catalog.demo_users[0]
    context = build_pair_context(
        model_key="autoencoder",
        selected_user_id=selected_demo.user_id,
        config=CONFIG,
        demo_mode=True,
    )

    summary = build_runtime_summary(context, demo_mode=True, config=CONFIG)

    assert summary.mode_label == "Built-in Demo Mode"
    assert summary.feature_row_count > 0
    assert summary.model_input_columns > 0
    assert summary.recommendation_count == CONFIG.ui.top_match_count


def test_runtime_health_rows_cover_expected_checks() -> None:
    demo_catalog = load_alias_catalog(demo_mode=True)
    selected_demo = demo_catalog.demo_users[0]
    context = build_pair_context(
        model_key="siamese",
        selected_user_id=selected_demo.user_id,
        config=CONFIG,
        demo_mode=True,
    )

    rows = build_runtime_health_rows(context, demo_mode=True, config=CONFIG)

    assert set(rows.columns) == {"Check", "Status", "Detail"}
    assert "Runtime mode" in rows["Check"].tolist()
    assert "Model artifacts" in rows["Check"].tolist()


def test_model_comparison_rows_cover_each_model_family() -> None:
    demo_catalog = load_alias_catalog(demo_mode=True)
    selected_demo = demo_catalog.demo_users[0]

    comparison = build_model_comparison_rows(
        selected_user_id=selected_demo.user_id,
        demo_mode=True,
        config=CONFIG,
    )

    assert set(comparison["model_key"]) == {family.key for family in CONFIG.model_families}
    assert not comparison["top_match_alias"].isna().any()
    assert not comparison["top_reason"].isna().any()
