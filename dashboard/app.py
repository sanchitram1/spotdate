from __future__ import annotations

import streamlit as st

from dashboard.components.description import render_description
from dashboard.components.implementation_ideas import render_implementation_ideas
from dashboard.components.title import render_title
from dashboard.components.top_visualization import render_top_visualization
from dashboard.config import CONFIG
from dashboard.services.contexts import build_pair_context, load_alias_catalog


def inject_styles() -> None:
    style = CONFIG.style
    st.markdown(
        f"""
        <style>
            .stApp {{
                background:
                    radial-gradient(circle at top left, rgba(94, 194, 255, 0.18), transparent 30%),
                    linear-gradient(180deg, {style.background} 0%, #050a13 100%);
                color: {style.text_primary};
            }}
            .hero-panel, .info-card, .flow-card, .idea-header, .pair-summary, .axis-note {{
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 20px;
                background: rgba(15, 27, 45, 0.85);
                backdrop-filter: blur(10px);
            }}
            .hero-panel {{
                padding: 1.8rem;
                background:
                    radial-gradient(circle at top right, rgba(246, 80, 143, 0.18), transparent 35%),
                    rgba(15, 27, 45, 0.88);
                margin-bottom: 1.25rem;
            }}
            .hero-panel h1, .idea-header h3, .pair-summary h3, .flow-card h4, .info-card h3 {{
                color: {style.text_primary};
                margin-bottom: 0.35rem;
            }}
            .hero-subtitle, .idea-header p, .pair-summary p, .info-card p, .flow-card p, .axis-note {{
                color: {style.text_muted};
            }}
            .eyebrow, .card-kicker, .idea-kicker {{
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-size: 0.75rem;
                color: {style.accent_tertiary};
                margin-bottom: 0.35rem;
            }}
            .hero-badges {{
                display: flex;
                gap: 0.75rem;
                flex-wrap: wrap;
                margin-top: 1rem;
            }}
            .hero-badges span, .mini-stats span {{
                display: inline-block;
                padding: 0.35rem 0.75rem;
                border-radius: 999px;
                background: rgba(255, 255, 255, 0.08);
                color: {style.text_primary};
                font-size: 0.85rem;
            }}
            .info-card, .idea-header, .pair-summary, .axis-note {{
                padding: 1rem 1.1rem;
            }}
            .flow-card {{
                padding: 1rem;
                background:
                    linear-gradient(180deg, rgba(246, 80, 143, 0.14), rgba(77, 215, 168, 0.08)),
                    rgba(15, 27, 45, 0.88);
                margin-bottom: 0.65rem;
            }}
            .mini-stats {{
                display: flex;
                flex-direction: column;
                gap: 0.4rem;
                margin-top: 0.75rem;
            }}
            .pair-summary {{
                margin-bottom: 1rem;
            }}
            .axis-note {{
                margin-bottom: 0.75rem;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> tuple[str, str]:
    alias_catalog = load_alias_catalog()
    model_labels = CONFIG.model_labels()

    st.sidebar.header("Explore a Match")
    selected_model = st.sidebar.selectbox(
        "Model family",
        options=[family.key for family in CONFIG.model_families],
        format_func=lambda key: model_labels[key],
    )

    selected_alias = st.sidebar.selectbox(
        "Demo user alias",
        options=[option.alias for option in alias_catalog.demo_users],
    )

    selected_demo = next(
        option for option in alias_catalog.demo_users if option.alias == selected_alias
    )
    st.sidebar.caption(selected_demo.blurb)

    return selected_model, selected_demo.user_id


def main() -> None:
    st.set_page_config(
        page_title=CONFIG.ui.app_title,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_styles()

    model_key, selected_user_id = render_sidebar()

    with st.spinner("Building match story from saved model artifacts..."):
        context = build_pair_context(
            model_key=model_key, selected_user_id=selected_user_id
        )

    render_title(context)
    render_description(context)
    render_top_visualization(context)
    render_implementation_ideas(context)


if __name__ == "__main__":
    main()
