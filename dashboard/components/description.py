from __future__ import annotations

import streamlit as st

from dashboard.config import CONFIG, DashboardConfig
from dashboard.types import PairContext


def render_description(context: PairContext, config: DashboardConfig = CONFIG) -> None:
    family_summary = next(
        family.summary
        for family in config.model_families
        if family.key == context.model_key
    )

    st.markdown("## Model Story")
    st.markdown(config.ui.app_description)

    step_columns = st.columns(3)
    step_columns[0].markdown(
        """
        <div class="info-card">
            <p class="card-kicker">Past</p>
            <h3>Feature Extraction</h3>
            <p>Aggregate each user's historical listening behavior into a numeric profile.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    step_columns[1].markdown(
        f"""
        <div class="info-card">
            <p class="card-kicker">Model</p>
            <h3>{context.model_label}</h3>
            <p>{family_summary}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    step_columns[2].markdown(
        """
        <div class="info-card">
            <p class="card-kicker">Future</p>
            <h3>Alignment Labels</h3>
            <p>Score pair compatibility by whether users eventually move toward similar music.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
