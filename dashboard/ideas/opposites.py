from __future__ import annotations

from dataclasses import dataclass

import plotly.graph_objects as go
import pandas as pd
import streamlit as st

from dashboard.config import CONFIG, DashboardConfig
from dashboard.ideas.base import ImplementationIdea
from dashboard.types import PairContext


@dataclass(frozen=True)
class OppositesPayload:
    differences: pd.DataFrame


class OppositesIdea(ImplementationIdea):
    key = "opposites"
    title = "Opposites Attract"
    kind = "Divergent Tension"
    description = (
        "Highlights where the pair is most different. A horizontal tug-of-war (dumbbell chart) showing "
        "the complementary tensions that make the relationship interesting."
    )

    def build(
        self, context: PairContext, config: DashboardConfig = CONFIG
    ) -> OppositesPayload:
        df = context.group_rankings.copy()
        df["diff_magnitude"] = abs(df["selected_score"] - df["match_score"])

        # Sort by maximum distance and pick top 3
        top_diffs = (
            df.sort_values("diff_magnitude", ascending=False)
            .head(3)
            .reset_index(drop=True)
        )
        return OppositesPayload(differences=top_diffs)

    def render(
        self,
        payload: OppositesPayload,
        context: PairContext,
        config: DashboardConfig = CONFIG,
    ) -> None:
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

        figure = go.Figure()

        # Reverse list for top-down plotting in Plotly
        y_labels = payload.differences["label"].tolist()[::-1]

        selected_vals = []
        match_vals = []

        for _, row in payload.differences.iloc[::-1].iterrows():
            selected_vals.append(row["selected_score"])
            match_vals.append(row["match_score"])

        figure.add_trace(
            go.Scatter(
                x=selected_vals,
                y=y_labels,
                mode="markers+text",
                name=context.selected_alias,
                marker=dict(color=config.style.accent, size=18),
            )
        )

        figure.add_trace(
            go.Scatter(
                x=match_vals,
                y=y_labels,
                mode="markers+text",
                name=context.match_alias,
                marker=dict(color=config.style.accent_secondary, size=18),
            )
        )

        # Add connecting lines (the "dumbbell" bar)
        for i in range(len(y_labels)):
            figure.add_shape(
                type="line",
                x0=selected_vals[i],
                y0=y_labels[i],
                x1=match_vals[i],
                y1=y_labels[i],
                line=dict(color=config.style.text_muted, width=3, dash="dot"),
                layer="below",
            )

        figure.update_layout(
            xaxis=dict(
                range=[0, 1],
                tickformat=".0%",
                title="Percentile Score",
                gridcolor="rgba(255,255,255,0.1)",
            ),
            yaxis=dict(gridcolor="rgba(0,0,0,0)"),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin={"l": 20, "r": 20, "t": 20, "b": 20},
            showlegend=True,
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5
            ),
        )

        st.plotly_chart(figure, use_container_width=True)
