from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from dashboard.config import CONFIG, DashboardConfig
from dashboard.types import PairContext


def _normalize_score(value: Any) -> float | None:
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None

    if numeric <= 1.0:
        return max(0.0, min(1.0, numeric))
    if numeric <= 100.0:
        return max(0.0, min(1.0, numeric / 100.0))
    return None


def _format_percent(value: Any) -> str:
    normalized = _normalize_score(value)
    if normalized is None:
        return "—"
    return f"{normalized:.0%}"


def _safe_label(value: Any, fallback: str = "Unknown") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def _pick_group_rows(
    group_rankings: pd.DataFrame,
) -> tuple[pd.Series | None, pd.Series | None]:
    if group_rankings.empty:
        return None, None
    return group_rankings.iloc[0], group_rankings.iloc[-1]


def _extract_label(row: pd.Series | None) -> str:
    if row is None:
        return "Shared Taste"
    for key in ("label", "group_label", "Group", "group", "key"):
        if key in row.index:
            return _safe_label(row[key], "Shared Taste")
    return "Shared Taste"


def _extract_description(row: pd.Series | None, fallback: str) -> str:
    if row is None:
        return fallback
    for key in ("story_lead", "description", "story", "summary"):
        if key in row.index and pd.notna(row[key]):
            return str(row[key])
    return fallback


def _build_story_line(
    selected_alias: str,
    match_alias: str,
    top_label: str,
    bottom_label: str,
) -> str:
    return (
        f"{selected_alias} and {match_alias} overlap most on {top_label.lower()}, "
        f"while {bottom_label.lower()} adds a little contrast to the pairing."
    )


def _card(title: str, value: str, body: str) -> str:
    return f"""
    <div class="info-card story-card">
        <div class="card-kicker">{title}</div>
        <h3>{value}</h3>
        <p>{body}</p>
    </div>
    """


def render_top_visualization(
    context: PairContext,
    config: DashboardConfig = CONFIG,
) -> None:
    top_row, bottom_row = _pick_group_rows(context.group_rankings)

    top_label = _extract_label(top_row)
    top_description = _extract_description(
        top_row,
        "This is the strongest shared dimension in the match.",
    )

    bottom_label = _extract_label(bottom_row)
    bottom_description = _extract_description(
        bottom_row,
        "This is where the two users feel the most different.",
    )

    story_line = _build_story_line(
        context.selected_alias,
        context.match_alias,
        top_label,
        bottom_label,
    )

    snapshot_text = f"{_format_percent(context.predicted_similarity)} model confidence"
    if context.future_alignment_score is not None:
        snapshot_text += (
            f" · {_format_percent(context.future_alignment_score)} future alignment"
        )

    st.markdown("## Top Visualization")
    st.markdown(
        f"""
        <div class="pair-summary">
            <div class="card-kicker">Match Story</div>
            <h3>{context.selected_alias} × {context.match_alias}</h3>
            <p>{story_line}</p>
            <div class="mini-stats">
                <span>Model: {context.model_label}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            _card(
                "Top Shared Trait",
                top_label,
                top_description,
            ),
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            _card(
                "Strongest Alignment",
                _format_percent(context.predicted_similarity),
                f"{context.selected_alias} and {context.match_alias} are most in sync on {top_label.lower()}.",
            ),
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            _card(
                "Biggest Tension",
                bottom_label,
                bottom_description,
            ),
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            _card(
                "Match Snapshot",
                snapshot_text,
                "A compact read of model confidence and projected long-term alignment.",
            ),
            unsafe_allow_html=True,
        )

    with st.expander("Advanced model view"):
        st.markdown("### Top 5 Recommendations")
        table = context.top_matches.drop(columns=["user_id"]).copy()
        st.dataframe(
            table,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Predicted Similarity": st.column_config.NumberColumn(format="%.3f"),
                "Future Alignment": st.column_config.NumberColumn(format="%.3f"),
            },
        )
