from __future__ import annotations

from dataclasses import dataclass

import plotly.graph_objects as go
import pandas as pd
import streamlit as st

from dashboard.config import CONFIG, DashboardConfig
from dashboard.ideas.base import ImplementationIdea
from dashboard.types import PairContext


@dataclass(frozen=True)
class DNAPayload:
    dna_pieces: pd.DataFrame


class MatchDNAIdea(ImplementationIdea):
    key = "match_dna"
    title = "Match DNA"
    kind = "Composition Chart"
    description = (
        "Visualizes the top reasons this pair was matched as a 'Relationship DNA' composition. "
        "Shows exactly what percentage of their compatibility comes from which shared trait."
    )

    def build(
        self, context: PairContext, config: DashboardConfig = CONFIG
    ) -> DNAPayload:
        # Take the top 4 semantic groups based on pair_score
        top_groups = context.group_rankings.head(4).copy()

        # Normalize the scores so they add up to 1 (100%)
        total_score = top_groups["pair_score"].sum()
        top_groups["dna_percentage"] = top_groups["pair_score"] / total_score

        return DNAPayload(dna_pieces=top_groups)

    def render(
        self,
        payload: DNAPayload,
        context: PairContext,
        config: DashboardConfig = CONFIG,
    ) -> None:
        figure = go.Figure(
            data=[
                go.Pie(
                    labels=payload.dna_pieces["label"],
                    values=payload.dna_pieces["dna_percentage"],
                    hole=0.6,
                    textinfo="label+percent",
                    hoverinfo="label+percent+text",
                    text=payload.dna_pieces["description"],
                    marker=dict(
                        colors=[
                            config.style.accent,
                            config.style.accent_secondary,
                            config.style.accent_tertiary,
                            config.style.text_primary,
                        ]
                    ),
                )
            ]
        )

        figure.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin={"l": 20, "r": 20, "t": 20, "b": 20},
            showlegend=False,
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

        chart_col, text_col = st.columns((1.2, 1.0))
        with chart_col:
            st.plotly_chart(figure, use_container_width=True)

        with text_col:
            st.markdown("### The DNA Breakdown")
            for _, row in payload.dna_pieces.iterrows():
                st.markdown(
                    f"""
                    <div class="axis-note">
                        <strong>{row["dna_percentage"]:.0%} {row["label"]}</strong><br>
                        <span style="color: {config.style.text_muted}">{row["story_lead"]}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
