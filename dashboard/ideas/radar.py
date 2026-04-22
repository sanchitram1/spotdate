from __future__ import annotations

from dataclasses import dataclass

import plotly.graph_objects as go
import pandas as pd
import streamlit as st

from dashboard.config import CONFIG, DashboardConfig
from dashboard.ideas.base import ImplementationIdea
from dashboard.types import PairContext


@dataclass(frozen=True)
class RadarPayload:
    axes: pd.DataFrame


class RadarIdea(ImplementationIdea):
    key = "radar"
    title = "Radar"
    kind = "Dynamic Pair Axis"
    description = (
        "A pair-specific radar chart that surfaces the strongest shared taste axes "
        "instead of forcing the same fixed dimensions on every match."
    )

    def build(
        self, context: PairContext, config: DashboardConfig = CONFIG
    ) -> RadarPayload:
        return RadarPayload(
            axes=context.group_rankings.head(config.ui.radar_axis_count).copy()
        )

    def render(
        self,
        payload: RadarPayload,
        context: PairContext,
        config: DashboardConfig = CONFIG,
    ) -> None:
        figure = go.Figure()

        axis_labels = payload.axes["label"].tolist()
        selected_values = payload.axes["selected_score"].tolist()
        match_values = payload.axes["match_score"].tolist()

        figure.add_trace(
            go.Scatterpolar(
                r=selected_values + [selected_values[0]],
                theta=axis_labels + [axis_labels[0]],
                fill="toself",
                name=context.selected_alias,
                line={"color": config.style.accent},
            )
        )
        figure.add_trace(
            go.Scatterpolar(
                r=match_values + [match_values[0]],
                theta=axis_labels + [axis_labels[0]],
                fill="toself",
                name=context.match_alias,
                line={"color": config.style.accent_secondary},
            )
        )

        figure.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            polar={
                "bgcolor": "rgba(0,0,0,0)",
                "radialaxis": {"visible": True, "range": [0, 1]},
            },
            margin={"l": 20, "r": 20, "t": 20, "b": 20},
        )

        st.markdown(
            f"""
            <div class="idea-header">
                <p class="idea-kicker">{self.kind}</p>
                <h3>{self.title}</h3>
                <p>{self.description}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        chart_column, text_column = st.columns((1.3, 1.0))
        with chart_column:
            st.plotly_chart(figure, use_container_width=True)

        with text_column:
            st.markdown("### Why these axes?")
            for _, row in payload.axes.iterrows():
                st.markdown(
                    f"""
                    <div class="axis-note">
                        <strong>{row["label"]}</strong><br>
                        Pair score: {row["pair_score"]:.0%}<br>
                        {row["description"]}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
