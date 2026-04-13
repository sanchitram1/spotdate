from __future__ import annotations

import streamlit as st

from dashboard.config import CONFIG, DashboardConfig
from dashboard.ideas.registry import get_implementation_ideas
from dashboard.types import PairContext


def render_implementation_ideas(
    context: PairContext,
    config: DashboardConfig = CONFIG,
) -> None:
    st.markdown(f"## {config.ui.implementation_section_title}")
    st.markdown(
        "Each section below is driven by the selected user's model-predicted match, "
        "so the product story changes when you swap the user alias or the model family."
    )

    for idea in get_implementation_ideas():
        payload = idea.build(context, config)
        idea.render(payload, context, config)
