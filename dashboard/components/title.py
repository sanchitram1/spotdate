from __future__ import annotations

import streamlit as st

from dashboard.config import CONFIG, DashboardConfig
from dashboard.types import PairContext


def render_title(context: PairContext, config: DashboardConfig = CONFIG) -> None:
    lead_reason = (
        str(context.group_rankings.iloc[0]["label"])
        if not context.group_rankings.empty
        else "No explanation available"
    )
    st.markdown(
        f"""
        <div class="hero-panel">
            <p class="eyebrow">Spotdate Product Story</p>
            <h1>{config.ui.app_title}</h1>
            <p class="hero-subtitle">{config.ui.app_subtitle}</p>
            <div class="hero-intro">
                <p class="hero-intro-heading">{config.ui.hero_intro_heading}</p>
                <p class="hero-intro-body">{config.ui.hero_intro_body}</p>
            </div>
            <div class="hero-badges">
                <span>{context.model_label}</span>
                <span>Selected: {context.selected_alias}</span>
                <span>Top match: {context.match_alias}</span>
                <span>Top signal: {lead_reason}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
