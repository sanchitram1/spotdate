from __future__ import annotations

import streamlit as st

from dashboard.config import CONFIG, DashboardConfig
from dashboard.ideas.registry import get_implementation_ideas
from dashboard.types import PairContext


def render_implementation_ideas(
    context: PairContext,
    config: DashboardConfig = CONFIG,
) -> None:
    ideas = get_implementation_ideas()
    review_order = " · ".join(
        f"{index}. {idea.title}" for index, idea in enumerate(ideas, start=1)
    )

    st.markdown(f"## {config.ui.implementation_section_title}")
    st.markdown(
        "Each concept below is stacked in presentation order so the team can review the "
        "full set of directions in one pass. Every module still runs off the selected "
        "user and model family, so the story changes when you swap either input."
    )
    st.caption(f"Review order: {review_order}")

    for index, idea in enumerate(ideas, start=1):
        st.markdown(f"### Concept {index:02d}")
        payload = idea.build(context, config)
        idea.render(payload, context, config)
        if index < len(ideas):
            st.divider()
