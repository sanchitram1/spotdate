from __future__ import annotations

import streamlit as st

from dashboard.components.data_health import render_data_health
from dashboard.components.description import render_description
from dashboard.components.implementation_ideas import render_implementation_ideas
from dashboard.components.model_comparison import render_model_comparison
from dashboard.components.title import render_title
from dashboard.components.top_visualization import render_top_visualization
from dashboard.config import CONFIG
from dashboard.services.contexts import build_pair_context, load_alias_catalog
from dashboard.services.data import inspect_artifact_status


def _display_path(path: str) -> str:
    from pathlib import Path

    try:
        return str(Path(path).resolve().relative_to(CONFIG.paths.repo_root))
    except ValueError:
        return path


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
            .hero-panel, .info-card, .flow-card, .idea-header, .pair-summary, .axis-note, .error-panel, .status-card {{
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
            .hero-intro {{
                margin-top: 1.25rem;
                margin-bottom: 1.15rem;
                max-width: 900px;
                padding: 1rem 1.2rem 1rem 1.35rem;
                border-left: 3px solid {style.accent_tertiary};
                background:
                    linear-gradient(90deg, rgba(255, 255, 255, 0.06), rgba(255, 255, 255, 0.02)),
                    rgba(8, 17, 31, 0.55);
                border-radius: 18px;
                box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
            }}
            .hero-panel h1, .idea-header h3, .pair-summary h3, .flow-card h4, .info-card h3, .error-panel h3, .status-card h3 {{
                color: {style.text_primary};
                margin-bottom: 0.35rem;
            }}
            .hero-subtitle, .idea-header p, .pair-summary p, .info-card p, .flow-card p, .axis-note, .error-panel p, .status-card p {{
                color: {style.text_muted};
            }}
            .hero-intro-heading {{
                margin: 0 0 0.45rem 0;
                font-size: 1.55rem;
                line-height: 1.2;
                font-weight: 700;
                color: {style.text_primary};
            }}
            .hero-intro-body {{
                margin: 0;
                font-size: 1.02rem;
                line-height: 1.7;
                color: {style.text_primary};
                max-width: 60ch;
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
            .info-card, .idea-header, .pair-summary, .axis-note, .error-panel, .status-card {{
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
            .health-list {{
                margin-top: 0.75rem;
                margin-bottom: 0;
                padding-left: 1.25rem;
                color: {style.text_muted};
            }}
            .error-panel {{
                margin-top: 1rem;
                background:
                    radial-gradient(circle at top right, rgba(246, 80, 143, 0.18), transparent 35%),
                    rgba(40, 16, 28, 0.92);
            }}
            .status-card {{
                margin-bottom: 1.1rem;
                padding: 1.1rem 1.2rem;
                background:
                    radial-gradient(circle at top right, rgba(94, 194, 255, 0.14), transparent 30%),
                    linear-gradient(135deg, rgba(18, 36, 28, 0.98), rgba(27, 38, 24, 0.96));
                border: 1px solid rgba(77, 215, 168, 0.18);
                box-shadow: 0 18px 45px rgba(0, 0, 0, 0.18);
            }}
            .status-card.demo {{
                border-left: 4px solid {style.accent};
            }}
            .status-card.ready {{
                border-left: 4px solid {style.accent_tertiary};
            }}
            .status-kicker {{
                margin: 0 0 0.35rem 0;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-size: 0.72rem;
                color: {style.accent_tertiary};
            }}
            .status-card h3 {{
                margin: 0 0 0.35rem 0;
                font-size: 1.15rem;
            }}
            .status-card p {{
                margin: 0;
                line-height: 1.55;
            }}
            .status-files {{
                display: flex;
                flex-wrap: wrap;
                gap: 0.55rem;
                margin-top: 0.9rem;
            }}
            .status-file {{
                display: inline-flex;
                align-items: center;
                padding: 0.42rem 0.7rem;
                border-radius: 999px;
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.08);
                color: {style.text_primary};
                font-size: 0.86rem;
                font-family: Consolas, "Courier New", monospace;
                white-space: nowrap;
            }}
            @media (max-width: 900px) {{
                .hero-intro-heading {{
                    font-size: 1.25rem;
                }}
                .hero-intro-body {{
                    font-size: 0.96rem;
                }}
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_runtime_banner(demo_mode: bool) -> None:
    status = inspect_artifact_status()
    if demo_mode and status.ready:
        st.markdown(
            """
            <div class="status-card ready">
                <p class="status-kicker">Runtime Status</p>
                <h3>Demo mode is active</h3>
                <p>The dashboard is using built-in sample data so you can keep working on the product experience.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    if demo_mode:
        missing_paths = "".join(
            f'<span class="status-file">{_display_path(path).replace("\\", "/")}</span>'
            for path in status.missing_paths
        )
        st.markdown(
            f"""
            <div class="status-card demo">
                <p class="status-kicker">Runtime Status</p>
                <h3>Demo mode is active</h3>
                <p>
                    Real training artifacts are not loaded yet, so this dashboard is showing a deterministic sample experience.
                    Add the files below to switch back to live model outputs.
                </p>
                <div class="status-files">
                    {missing_paths}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        """
        <div class="status-card ready">
            <p class="status-kicker">Runtime Status</p>
            <h3>Saved artifacts detected</h3>
            <p>The dashboard is using the real feature table, edgelist, and model files.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> tuple[str, str, bool]:
    status = inspect_artifact_status()
    forced_demo_mode = not status.ready
    allow_demo_toggle = status.ready

    demo_mode = forced_demo_mode
    if allow_demo_toggle:
        demo_mode = st.sidebar.toggle(
            "Use built-in demo mode",
            value=False,
            help="Useful when you want to iterate on the UI without loading the saved training artifacts.",
        )

    alias_catalog = load_alias_catalog(demo_mode=demo_mode)
    model_labels = CONFIG.model_labels()

    st.sidebar.header("Explore a Match")
    if forced_demo_mode:
        st.sidebar.warning(
            "Saved artifacts are missing. Demo mode has been enabled automatically."
        )
    elif demo_mode:
        st.sidebar.info(
            "Demo mode is enabled. The app is using built-in sample users and scores."
        )

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

    return selected_model, selected_demo.user_id, demo_mode


def render_dashboard_error(error: Exception, demo_mode: bool) -> None:
    mode_label = "demo mode" if demo_mode else "artifact mode"
    st.markdown(
        f"""
        <div class="error-panel">
            <p class="card-kicker">Dashboard State</p>
            <h3>We could not build the match view</h3>
            <p>
                The dashboard hit an error while assembling the pair context in {mode_label}.
                This usually means a required artifact, expected feature column, or model metadata field is missing.
            </p>
            <p><strong>Error:</strong> {type(error).__name__}: {error}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(
        page_title=CONFIG.ui.app_title,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_styles()

    model_key, selected_user_id, demo_mode = render_sidebar()
    render_runtime_banner(demo_mode)

    spinner_message = (
        "Building match story from built-in demo data..."
        if demo_mode
        else "Building match story from saved model artifacts..."
    )

    try:
        with st.spinner(spinner_message):
            context = build_pair_context(
                model_key=model_key,
                selected_user_id=selected_user_id,
                demo_mode=demo_mode,
            )
    except Exception as error:
        render_dashboard_error(error, demo_mode)
        return

    render_title(context)
    render_description(context)
    render_data_health(context, demo_mode)
    render_model_comparison(selected_user_id, demo_mode)
    render_top_visualization(context)
    render_implementation_ideas(context)


if __name__ == "__main__":
    main()
