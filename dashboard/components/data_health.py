from __future__ import annotations

import streamlit as st

from dashboard.config import CONFIG, DashboardConfig
from dashboard.services.data import inspect_artifact_status
from dashboard.services.overview import build_runtime_health_rows, build_runtime_summary
from dashboard.types import PairContext


def render_data_health(
    context: PairContext,
    demo_mode: bool,
    config: DashboardConfig = CONFIG,
) -> None:
    summary = build_runtime_summary(context, demo_mode, config)
    status = inspect_artifact_status(config)
    health_rows = build_runtime_health_rows(context, demo_mode, config)

    st.markdown("## Runtime Health")
    st.markdown(
        "This panel makes the dashboard's current state explicit so you can tell whether "
        "you're iterating on real saved artifacts or the built-in development fallback."
    )

    metric_columns = st.columns(4)
    metric_columns[0].metric("Mode", summary.mode_label)
    metric_columns[1].metric("Users", f"{summary.feature_row_count}")
    metric_columns[2].metric("Encoded Features", f"{summary.model_input_columns}")
    metric_columns[3].metric("Top Explanation", summary.top_explanation_label)

    left_column, right_column = st.columns((1.2, 1.0))

    with left_column:
        st.dataframe(
            health_rows,
            use_container_width=True,
            hide_index=True,
        )

    with right_column:
        missing_lines = (
            "".join(f"<li><code>{path}</code></li>" for path in status.missing_paths)
            if status.missing_paths
            else "<li>No missing artifact paths detected.</li>"
        )
        st.markdown(
            f"""
            <div class="info-card">
                <p class="card-kicker">Activation Checklist</p>
                <h3>What The App Still Needs</h3>
                <p>
                    The dashboard becomes fully artifact-backed when the feature table, future
                    alignment reference, and model manifests are all present.
                </p>
                <ul class="health-list">{missing_lines}</ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
