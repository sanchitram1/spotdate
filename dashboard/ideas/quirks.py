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
    green_flag_items: list["QuirkDisplayItem"]
    selected_quirk_items: list["QuirkDisplayItem"]
    match_quirk_items: list["QuirkDisplayItem"]


@dataclass(frozen=True)
class QuirkDisplayItem:
    key: str
    text: str


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
        del config
        green_flags = []
        selected_quirks = []
        match_quirks = []
        green_flag_items: list[QuirkDisplayItem] = []
        selected_quirk_items: list[QuirkDisplayItem] = []
        match_quirk_items: list[QuirkDisplayItem] = []

        HIGH_THRESH = 0.85
        LOW_THRESH = 0.15
        HIGH_AVG_THRES = 0.7
        LOW_AVG_THRES = 0.3

        for _, row in context.group_rankings.iterrows():
            s_score = row["selected_score"]
            m_score = row["match_score"]
            label = str(row["label"])
            key = self._normalize_key(label)

            # Shared Extremes (Green Flags)
            if s_score >= HIGH_THRESH and m_score >= HIGH_THRESH:
                green_flags.append(f"Way above average on {label}")
                green_flag_items.append(
                    QuirkDisplayItem(
                        key=key,
                        text=f"You both vibe on high {key.lower()} songs",
                    )
                )
            elif s_score <= LOW_THRESH and m_score <= LOW_THRESH:
                green_flags.append(f"Both heavily lean away from {label}")
                green_flag_items.append(
                    QuirkDisplayItem(
                        key=key,
                        text=f"You both lean away from {key.lower()} songs",
                    )
                )

            # Quirks (One is extreme, the other is normal/opposite)
            elif s_score >= HIGH_THRESH and m_score < HIGH_AVG_THRES:
                selected_quirks.append(f"Obsessed with {label}")
                selected_quirk_items.append(
                    QuirkDisplayItem(
                        key=key,
                        text=f"You gravitate hard toward {key.lower()} songs",
                    )
                )
            elif s_score <= LOW_THRESH and m_score > LOW_AVG_THRES:
                selected_quirks.append(f"Averse to {label}")
                selected_quirk_items.append(
                    QuirkDisplayItem(
                        key=key,
                        text=f"You gravitate away from {key.lower()} songs",
                    )
                )

            if m_score >= HIGH_THRESH and s_score < HIGH_AVG_THRES:
                match_quirks.append(f"Obsessed with {label}")
                match_quirk_items.append(
                    QuirkDisplayItem(
                        key=key,
                        text=f"They gravitate hard toward {key.lower()} songs",
                    )
                )
            elif m_score <= LOW_THRESH and s_score > LOW_AVG_THRES:
                match_quirks.append(f"Averse to {label}")
                match_quirk_items.append(
                    QuirkDisplayItem(
                        key=key,
                        text=f"They gravitate away from {key.lower()} songs",
                    )
                )

        if not green_flags:
            green_flags = ["No extremely unified traits"]
            green_flag_items = [
                QuirkDisplayItem(
                    key="Energy",
                    text="You both vibe on high energy songs",
                )
            ]
        if not selected_quirks:
            selected_quirks = ["Pretty well-rounded listener"]
            selected_quirk_items = [
                QuirkDisplayItem(
                    key="Mood",
                    text="You gravitate away from moody ones",
                )
            ]
        if not match_quirks:
            match_quirks = ["Pretty well-rounded listener"]
            match_quirk_items = [
                QuirkDisplayItem(
                    key="Mood",
                    text="They gravitate away from moody ones",
                )
            ]

        green_keys = frozenset(item.key for item in green_flag_items)
        selected_pairs = [
            (text, item)
            for text, item in zip(selected_quirks, selected_quirk_items, strict=True)
            if item.key not in green_keys
        ]
        if selected_pairs:
            selected_quirks = [text for text, _ in selected_pairs]
            selected_quirk_items = [item for _, item in selected_pairs]
        else:
            selected_quirks, selected_quirk_items = [], []

        if not selected_quirks:
            selected_quirks = ["Pretty well-rounded listener"]
            selected_quirk_items = [
                QuirkDisplayItem(
                    key="Mood",
                    text="You gravitate away from moody ones",
                )
            ]

        match_pairs = [
            (text, item)
            for text, item in zip(match_quirks, match_quirk_items, strict=True)
            if item.key not in green_keys
        ]
        if match_pairs:
            match_quirks = [text for text, _ in match_pairs]
            match_quirk_items = [item for _, item in match_pairs]
        else:
            match_quirks, match_quirk_items = [], []

        if not match_quirks:
            match_quirks = ["Pretty well-rounded listener"]
            match_quirk_items = [
                QuirkDisplayItem(
                    key="Mood",
                    text="They gravitate away from moody ones",
                )
            ]

        return QuirksPayload(
            green_flags=green_flags,
            selected_quirks=selected_quirks,
            match_quirks=match_quirks,
            green_flag_items=green_flag_items,
            selected_quirk_items=selected_quirk_items,
            match_quirk_items=match_quirk_items,
        )

    @staticmethod
    def _normalize_key(label: str) -> str:
        cleaned = " ".join(str(label).replace("_", " ").split()).strip()
        if not cleaned:
            return "Taste"
        return cleaned.title()

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
