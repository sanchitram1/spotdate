from __future__ import annotations

from dashboard.config import CONFIG
from dashboard.services.contexts import build_pair_context, load_alias_catalog
from dashboard.services.data import (
    inspect_artifact_status,
    load_demo_datasets_uncached,
)


def test_demo_datasets_cover_expected_runtime_columns() -> None:
    datasets = load_demo_datasets_uncached(CONFIG)

    assert not datasets.raw_features.empty
    assert "user_id" in datasets.raw_features.columns
    assert "user_type_loyal" in datasets.raw_features.columns
    assert datasets.demo_future_alignment_lookup
    assert datasets.full_edgelist_path == CONFIG.paths.full_edgelist_path


def test_demo_pair_context_builds_without_saved_artifacts() -> None:
    demo_catalog = load_alias_catalog(demo_mode=True)
    selected_demo = demo_catalog.demo_users[0]

    context = build_pair_context(
        model_key="autoencoder",
        selected_user_id=selected_demo.user_id,
        config=CONFIG,
        demo_mode=True,
    )

    assert context.selected_alias == selected_demo.alias
    assert context.match_alias
    assert not context.top_matches.empty
    assert context.model_spec.metadata["mode"] == "demo"


def test_artifact_status_reports_missing_inputs_in_current_workspace() -> None:
    status = inspect_artifact_status(CONFIG)

    assert isinstance(status.ready, bool)
    if not status.ready:
        assert status.missing_paths
