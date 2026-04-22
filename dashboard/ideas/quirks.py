from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

from dashboard.config import CONFIG, DashboardConfig
from dashboard.ideas.base import ImplementationIdea
from dashboard.types import PairContext


@dataclass(frozen=True)
class QuirksPayload:
    green_flags: list[str]
    selected_quirks: list[str]
    match_quirks: list[str]


class QuirksIdea(ImplementationIdea):
    key = "quirks"
    title = "Green Flags & Quirks"
    kind = "Bio Tags"
    description = (
        "Translates extreme listening habits into dating profile tags. Finds areas where they share an extreme "
        "trait (Green Flags) or where one person is uniquely strange (Quirks)."
    )

    def build(
        self, context: PairContext, config: DashboardConfig = CONFIG
    ) -> QuirksPayload:
        green_flags = []
        selected_quirks = []
        match_quirks = []

        HIGH_THRESH = 0.85
        LOW_THRESH = 0.15

        for _, row in context.group_rankings.iterrows():
            s_score = row["selected_score"]
            m_score = row["match_score"]
            label = row["label"]

            # Shared Extremes (Green Flags)
            if s_score >= HIGH_THRESH and m_score >= HIGH_THRESH:
                green_flags.append(f"Way above average on {label}")
            elif s_score <= LOW_THRESH and m_score <= LOW_THRESH:
                green_flags.append(f"Both heavily lean away from {label}")

            # Quirks (One is extreme, the other is normal/opposite)
            elif s_score >= HIGH_THRESH and m_score < 0.7:
                selected_quirks.append(f"Obsessed with {label}")
            elif s_score <= LOW_THRESH and m_score > 0.3:
                selected_quirks.append(f"Averse to {label}")

            if m_score >= HIGH_THRESH and s_score < 0.7:
                match_quirks.append(f"Obsessed with {label}")
            elif m_score <= LOW_THRESH and s_score > 0.3:
                match_quirks.append(f"Averse to {label}")

        return QuirksPayload(
            green_flags=green_flags if green_flags else ["No extremely unified traits"],
            selected_quirks=selected_quirks
            if selected_quirks
            else ["Pretty well-rounded listener"],
            match_quirks=match_quirks
            if match_quirks
            else ["Pretty well-rounded listener"],
        )

    def render(
        self,
        payload: QuirksPayload,
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

        col1, col2 = st.columns(2)

        html_template = """
        <div style="background: {bg}; padding: 15px; border-radius: 8px; margin-bottom: 10px;">
            <p style="margin:0; font-size: 0.9em; color: {muted}; text-transform: uppercase;"><strong>{header}</strong></p>
            <ul style="margin-top: 8px; margin-bottom: 0px; padding-left: 20px;">
                {items}
            </ul>
        </div>
        """

        with col1:
            items = "".join([f"<li>{gf}</li>" for gf in payload.green_flags])
            st.markdown(
                html_template.format(
                    bg=config.style.panel_background,
                    muted=config.style.accent,
                    header="💚 Shared Green Flags",
                    items=items,
                ),
                unsafe_allow_html=True,
            )

        with col2:
            s_items = "".join([f"<li>{q}</li>" for q in payload.selected_quirks])
            m_items = "".join([f"<li>{q}</li>" for q in payload.match_quirks])

            st.markdown(
                html_template.format(
                    bg=config.style.panel_background,
                    muted=config.style.text_muted,
                    header=f"🎭 {context.selected_alias}'s Quirks",
                    items=s_items,
                ),
                unsafe_allow_html=True,
            )

            st.markdown(
                html_template.format(
                    bg=config.style.panel_background,
                    muted=config.style.text_muted,
                    header=f"🎭 {context.match_alias}'s Quirks",
                    items=m_items,
                ),
                unsafe_allow_html=True,
            )
