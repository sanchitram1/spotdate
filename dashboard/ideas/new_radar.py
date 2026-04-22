from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import plotly.graph_objects as go
import pandas as pd
import streamlit as st
from sklearn.metrics.pairwise import cosine_similarity

from dashboard.config import CONFIG, DashboardConfig
from dashboard.ideas.base import ImplementationIdea
from dashboard.types import PairContext


@dataclass(frozen=True)
class RadarPayload:
    axes: pd.DataFrame


class NewRadarIdea(ImplementationIdea):
    key = "new_radar"
    title = "Radar (Cosine Similarity)"
    kind = "Dynamic Pair Axis"
    description = (
        "A pair-specific radar chart that surfaces the 2 top similar, 2 mid similar, and 2 least similar "
        "feature groups between the users based on cosine similarity."
    )

    def build(
        self, context: PairContext, config: DashboardConfig = CONFIG
    ) -> RadarPayload:
        group_similarities = []
        for group in config.semantic_groups:
            cols = [signal.column for signal in group.signals]
            cols = [c for c in cols if c in context.selected_profile.index]
            if not cols:
                continue

            vec1 = (
                context.selected_profile[cols]
                .fillna(0)
                .values.astype(float)
                .reshape(1, -1)
            )
            vec2 = (
                context.match_profile[cols]
                .fillna(0)
                .values.astype(float)
                .reshape(1, -1)
            )

            if np.all(vec1 == 0) and np.all(vec2 == 0):
                sim = 1.0
            elif np.all(vec1 == 0) or np.all(vec2 == 0):
                sim = 0.0
            else:
                sim = cosine_similarity(vec1, vec2)[0, 0]

            # We still want the ranker's base scores to draw the radar
            row = context.group_rankings[
                context.group_rankings["group_key"] == group.key
            ].iloc[0]

            group_similarities.append(
                {
                    "group_key": group.key,
                    "label": group.label,
                    "description": group.description,
                    "cosine_sim": float(sim),
                    "selected_score": row["selected_score"],
                    "match_score": row["match_score"],
                }
            )

        sim_df = pd.DataFrame(group_similarities)
        # Sort by cosine similarity descending
        sim_df = sim_df.sort_values("cosine_sim", ascending=False).reset_index(
            drop=True
        )

        n = len(sim_df)
        if n >= 6:
            top = sim_df.head(2).copy()
            top["similarity_category"] = "Top Similar"

            least = sim_df.tail(2).copy()
            least["similarity_category"] = "Least Similar"

            mid_idx = n // 2 - 1
            mid = sim_df.iloc[mid_idx : mid_idx + 2].copy()
            mid["similarity_category"] = "Mid Similar"

            axes = pd.concat([top, mid, least]).reset_index(drop=True)
        else:
            axes = sim_df.copy()
            axes["similarity_category"] = ""

        return RadarPayload(axes=axes)

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
            st.markdown("### Selected Features")
            for _, row in payload.axes.iterrows():
                category = row.get("similarity_category", "")
                cat_html = f"<em>{category}</em><br>" if category else ""
                st.markdown(
                    f"""
                    <div class="axis-note">
                        <strong>{row["label"]}</strong><br>
                        {cat_html}
                        Cosine Similarity: {row["cosine_sim"]:.0%}<br>
                        {row["description"]}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
