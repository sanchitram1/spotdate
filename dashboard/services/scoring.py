from __future__ import annotations

import re

import pandas as pd

from dashboard.config import CONFIG, DashboardConfig, SemanticGroupConfig


def humanize_column_name(column: str) -> str:
    column = column.replace("_", " ")
    column = re.sub(r"\s+", " ", column).strip()
    return column.title()


def _percentile_rank(series: pd.Series, invert: bool) -> pd.Series:
    ranked = series.rank(method="average", pct=True).fillna(0.5)
    if invert:
        return 1.0 - ranked
    return ranked


def build_user_group_scores(
    features: pd.DataFrame,
    config: DashboardConfig = CONFIG,
) -> pd.DataFrame:
    score_columns: dict[str, pd.Series] = {}

    for group in config.semantic_groups:
        weighted_scores = []
        total_weight = 0.0

        for signal in group.signals:
            if signal.column not in features.columns:
                raise KeyError(f"Missing semantic signal column: {signal.column}")

            ranked = _percentile_rank(features[signal.column], invert=signal.invert)
            weighted_scores.append(ranked * signal.weight)
            total_weight += signal.weight

        combined = sum(weighted_scores) / total_weight
        score_columns[group.key] = combined.clip(lower=0.0, upper=1.0)

    score_frame = pd.DataFrame(score_columns, index=features.index)
    score_frame.index.name = "user_id"
    return score_frame


def rank_pair_groups(
    selected_user_id: str,
    match_user_id: str,
    user_group_scores: pd.DataFrame,
    config: DashboardConfig = CONFIG,
) -> pd.DataFrame:
    rows = []

    for group in config.semantic_groups:
        selected_score = float(user_group_scores.loc[selected_user_id, group.key])
        match_score = float(user_group_scores.loc[match_user_id, group.key])
        closeness = 1.0 - abs(selected_score - match_score)
        distinctiveness = max(abs(selected_score - 0.5), abs(match_score - 0.5))
        pair_score = (0.7 * closeness) + (0.3 * distinctiveness)

        rows.append(
            {
                "group_key": group.key,
                "label": group.label,
                "description": group.description,
                "story_lead": group.story_lead,
                "selected_score": selected_score,
                "match_score": match_score,
                "closeness": closeness,
                "distinctiveness": distinctiveness,
                "pair_score": pair_score,
            }
        )

    ranked = (
        pd.DataFrame(rows)
        .sort_values("pair_score", ascending=False)
        .reset_index(drop=True)
    )
    return ranked


def build_metric_rows(
    group: SemanticGroupConfig,
    selected_profile: pd.Series,
    match_profile: pd.Series,
) -> pd.DataFrame:
    rows = []
    for signal in group.signals:
        rows.append(
            {
                "Metric": humanize_column_name(signal.column),
                "Selected": selected_profile[signal.column],
                "Match": match_profile[signal.column],
            }
        )
    return pd.DataFrame(rows)
