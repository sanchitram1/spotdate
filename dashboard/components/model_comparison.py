from __future__ import annotations

import streamlit as st

from dashboard.config import CONFIG, DashboardConfig
from dashboard.services.overview import build_model_comparison_rows


def render_model_comparison(
    selected_user_id: str,
    demo_mode: bool,
    config: DashboardConfig = CONFIG,
) -> None:
    comparison = build_model_comparison_rows(selected_user_id, demo_mode, config)

    st.markdown("## Model Comparison")
    st.markdown(
        "This section compares how each model family explains the same selected user, which "
        "makes it easier to debug product positioning and not just model score."
    )

    summary_columns = st.columns(len(comparison))
    for column, (_, row) in zip(summary_columns, comparison.iterrows(), strict=False):
        future_alignment = (
            f"{float(row['future_alignment_score']):.3f}"
            if row["future_alignment_score"] is not None
            else "N/A"
        )
        avg_score = (
            f"{float(row['avg_score']):.3f}" if row["avg_score"] is not None else "N/A"
        )
        with column:
            st.markdown(
                f"""
                <div class="info-card">
                    <p class="card-kicker">{row["model_key"]}</p>
                    <h3>{row["model_label"]}</h3>
                    <p>Top match: <strong>{row["top_match_alias"]}</strong></p>
                    <p>Predicted similarity: <strong>{float(row["predicted_similarity"]):.3f}</strong></p>
                    <p>Future alignment: <strong>{future_alignment}</strong></p>
                    <p>Average score: <strong>{avg_score}</strong></p>
                    <p>Top reason: <strong>{row["top_reason"]}</strong></p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    display = comparison.rename(
        columns={
            "model_key": "Model Key",
            "model_label": "Model Label",
            "top_match_alias": "Top Match",
            "predicted_similarity": "Predicted Similarity",
            "future_alignment_score": "Future Alignment",
            "top_reason": "Top Reason",
            "avg_score": "Average Score",
        }
    )

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Predicted Similarity": st.column_config.NumberColumn(format="%.3f"),
            "Future Alignment": st.column_config.NumberColumn(format="%.3f"),
            "Average Score": st.column_config.NumberColumn(format="%.3f"),
        },
    )
