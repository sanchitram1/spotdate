from __future__ import annotations

from typing import Any

import plotly.graph_objects as go
import streamlit as st

from dashboard.config import CONFIG, DashboardConfig
from dashboard.types import PairContext


def _format_metric(value: Any, percent: bool = False) -> str:
    if value is None:
        return "N/A"
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)

    if percent:
        return f"{numeric:.1%}"
    return f"{numeric:.3f}"


def _build_embedding_figure(context: PairContext) -> go.Figure:
    palette = {
        "Cohort": "rgba(157, 176, 200, 0.25)",
        "Selected": CONFIG.style.accent,
        "Match": CONFIG.style.accent_secondary,
    }

    figure = go.Figure()

    for role in ("Cohort", "Selected", "Match"):
        subset = context.projection[context.projection["role"] == role]
        figure.add_trace(
            go.Scatter(
                x=subset["x"],
                y=subset["y"],
                mode="markers",
                name=role,
                marker={
                    "size": 8 if role == "Cohort" else 16,
                    "color": palette[role],
                    "line": {"width": 1, "color": "#f4f7fb"}
                    if role != "Cohort"
                    else None,
                },
                text=subset["Alias"],
                customdata=subset[["Listener Profile"]],
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "Listener profile: %{customdata[0]}<br>"
                    "Embedding X: %{x:.2f}<br>"
                    "Embedding Y: %{y:.2f}<extra></extra>"
                ),
            )
        )

    figure.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 10, "r": 10, "t": 10, "b": 10},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0.0},
        xaxis={"title": "Embedding axis 1", "showgrid": False, "zeroline": False},
        yaxis={"title": "Embedding axis 2", "showgrid": False, "zeroline": False},
    )
    return figure


def render_top_visualization(
    context: PairContext, config: DashboardConfig = CONFIG
) -> None:
    metadata = context.model_spec.metadata
    future_alignment_text = (
        f" | Future alignment: <strong>{context.future_alignment_score:.3f}</strong>"
        if context.future_alignment_score is not None
        else " | Future alignment: <strong>N/A</strong>"
    )

    st.markdown("## Match Outcome")
    st.markdown(
        f"""
        <div class="pair-summary">
            <p class="idea-kicker">Selected Pair</p>
            <h3>{context.selected_alias} matches with {context.match_alias}</h3>
            <p>
                Predicted similarity: <strong>{context.predicted_similarity:.3f}</strong>
                {future_alignment_text}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    metric_columns = st.columns(4)
    metric_columns[0].metric(
        "Average Score",
        _format_metric(metadata.get("avg_score")),
    )
    metric_columns[1].metric(
        "Hit Rate @ K",
        _format_metric(metadata.get("hit_rate_at_k"), percent=True),
    )
    metric_columns[2].metric(
        "Precision @ High Score",
        _format_metric(metadata.get("precision_at_high_score"), percent=True),
    )
    metric_columns[3].metric(
        "Recall @ Top 5%",
        _format_metric(metadata.get("recall_at_top_5_percent"), percent=True),
    )

    plot_column, table_column = st.columns((1.6, 1.0))

    with plot_column:
        st.plotly_chart(_build_embedding_figure(context), use_container_width=True)

    with table_column:
        st.markdown("### Top Recommendations")
        if context.top_matches.empty:
            st.info(
                "No ranked recommendations were produced for the selected user. "
                "This usually means the available cohort is too small or the model artifacts are incomplete."
            )
        else:
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
