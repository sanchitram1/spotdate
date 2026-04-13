from __future__ import annotations

import streamlit as st

from dashboard.config import CONFIG, DashboardConfig
from dashboard.types import PairContext


def render_title(context: PairContext, config: DashboardConfig = CONFIG) -> None:
    st.markdown(
        f"""
        <div class="hero-panel">
            <p class="eyebrow">Spotdate Product Story</p>
            <h1>{config.ui.app_title}</h1>
            <p class="hero-subtitle">{config.ui.app_subtitle}</p>
            <div class="hero-badges">
                <span>{context.model_label}</span>
                <span>{context.selected_alias} → {context.match_alias}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
