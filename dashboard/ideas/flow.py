from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from dashboard.config import CONFIG, DashboardConfig
from dashboard.ideas.base import ImplementationIdea
from dashboard.services.scoring import build_metric_rows
from dashboard.types import PairContext


@dataclass(frozen=True)
class FlowCardPayload:
    label: str
    summary: str
    pair_score: float
    selected_score: float
    match_score: float
    metrics: pd.DataFrame


class FlowIdea(ImplementationIdea):
    key = "flow"
    title = "Flow"
    kind = "Wrapped-style Story"
    description = (
        "A sequence of factual story cards that turns pair alignment into bite-sized, "
        "Spotify Wrapped-like product moments."
    )

    def build(
        self, context: PairContext, config: DashboardConfig = CONFIG
    ) -> list[FlowCardPayload]:
        group_lookup = {group.key: group for group in config.semantic_groups}
        payloads: list[FlowCardPayload] = []

        for _, row in context.group_rankings.head(config.ui.flow_card_count).iterrows():
            group = group_lookup[row["group_key"]]
            payloads.append(
                FlowCardPayload(
                    label=row["label"],
                    summary=(
                        f"{context.selected_alias} and {context.match_alias} align on "
                        f"{row['label'].lower()}. {row['story_lead']}"
                    ),
                    pair_score=float(row["pair_score"]),
                    selected_score=float(row["selected_score"]),
                    match_score=float(row["match_score"]),
                    metrics=build_metric_rows(
                        group=group,
                        selected_profile=context.selected_profile,
                        match_profile=context.match_profile,
                    ),
                )
            )

        return payloads

    def render(
        self,
        payload: list[FlowCardPayload],
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

        columns = st.columns(len(payload))
        for column, card in zip(columns, payload, strict=False):
            with column:
                st.markdown(
                    f"""
                    <div class="flow-card">
                        <p class="card-kicker">{card.label}</p>
                        <h4>{card.pair_score:.0%} alignment</h4>
                        <p>{card.summary}</p>
                        <div class="mini-stats">
                            <span>{context.selected_alias}: {card.selected_score:.0%}</span>
                            <span>{context.match_alias}: {card.match_score:.0%}</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.dataframe(
                    card.metrics,
                    use_container_width=True,
                    hide_index=True,
                )
