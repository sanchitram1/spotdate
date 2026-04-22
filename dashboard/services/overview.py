from __future__ import annotations

import pandas as pd

from dashboard.config import CONFIG, DashboardConfig
from dashboard.services.contexts import build_pair_context
from dashboard.services.data import (
    inspect_artifact_status,
    load_app_datasets,
    load_demo_datasets,
)
from dashboard.types import ModelComparisonRow, PairContext, RuntimeSummary


def build_runtime_summary(
    context: PairContext,
    demo_mode: bool,
    config: DashboardConfig = CONFIG,
) -> RuntimeSummary:
    datasets = load_demo_datasets() if demo_mode else load_app_datasets()
    top_explanation_label = (
        str(context.group_rankings.iloc[0]["label"])
        if not context.group_rankings.empty
        else "No ranked explanation available"
    )
    return RuntimeSummary(
        mode_label="Built-in Demo Mode" if demo_mode else "Saved Artifact Mode",
        feature_row_count=int(datasets.raw_features.shape[0]),
        model_input_rows=int(datasets.model_matrix.shape[0]),
        model_input_columns=int(datasets.model_matrix.shape[1]),
        semantic_group_count=len(config.semantic_groups),
        recommendation_count=int(context.top_matches.shape[0]),
        top_explanation_label=top_explanation_label,
    )


def build_runtime_health_rows(
    context: PairContext,
    demo_mode: bool,
    config: DashboardConfig = CONFIG,
) -> pd.DataFrame:
    summary = build_runtime_summary(context, demo_mode, config)
    status = inspect_artifact_status(config)

    rows = [
        {
            "Check": "Runtime mode",
            "Status": summary.mode_label,
            "Detail": (
                "Using deterministic built-in sample artifacts."
                if demo_mode
                else "Using saved features, edgelists, and trained model files."
            ),
        },
        {
            "Check": "Feature table",
            "Status": "Ready" if status.features_available else "Missing",
            "Detail": f"{summary.feature_row_count} users available to the dashboard.",
        },
        {
            "Check": "Future alignment reference",
            "Status": "Ready" if status.full_edgelist_available or demo_mode else "Missing",
            "Detail": f"{summary.recommendation_count} recommendations generated for the selected user.",
        },
        {
            "Check": "Model artifacts",
            "Status": "Ready" if status.experiments_available or demo_mode else "Missing",
            "Detail": (
                ", ".join(status.available_model_keys)
                if status.available_model_keys and not demo_mode
                else "Autoencoder and Siamese demo loaders are available."
            ),
        },
        {
            "Check": "Semantic explanations",
            "Status": "Ready",
            "Detail": (
                f"{summary.semantic_group_count} groups scored. Top explanation: "
                f"{summary.top_explanation_label}."
            ),
        },
        {
            "Check": "Model input matrix",
            "Status": "Ready",
            "Detail": (
                f"{summary.model_input_rows} rows x {summary.model_input_columns} encoded features."
            ),
        },
    ]
    return pd.DataFrame(rows)


def build_model_comparison_rows(
    selected_user_id: str,
    demo_mode: bool,
    config: DashboardConfig = CONFIG,
) -> pd.DataFrame:
    rows: list[ModelComparisonRow] = []
    for family in config.model_families:
        context = build_pair_context(
            model_key=family.key,
            selected_user_id=selected_user_id,
            config=config,
            demo_mode=demo_mode,
        )
        top_reason = (
            str(context.group_rankings.iloc[0]["label"])
            if not context.group_rankings.empty
            else "No ranked explanation"
        )
        avg_score_raw = context.model_spec.metadata.get("avg_score")
        avg_score = float(avg_score_raw) if avg_score_raw is not None else None
        rows.append(
            ModelComparisonRow(
                model_key=family.key,
                model_label=context.model_label,
                top_match_alias=context.match_alias,
                predicted_similarity=float(context.predicted_similarity),
                future_alignment_score=context.future_alignment_score,
                top_reason=top_reason,
                avg_score=avg_score,
            )
        )

    comparison = pd.DataFrame([row.__dict__ for row in rows])
    return comparison.sort_values(
        by=["predicted_similarity", "avg_score"], ascending=False
    ).reset_index(drop=True)
