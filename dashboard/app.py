from __future__ import annotations

import re
import sys
from pathlib import Path

import streamlit as st

# Ensure `uv run streamlit run dashboard/app.py` can resolve the package imports.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dashboard.components.implementation_ideas import (  # noqa: E402
    render_implementation_ideas_grid,
    render_model_explanation_section,
)
from dashboard.config import CONFIG  # noqa: E402
from dashboard.services.contexts import (  # noqa: E402
    build_pair_context,
    load_alias_catalog,
)
from dashboard.services.data import inspect_artifact_status  # noqa: E402


def _display_path(path: str) -> str:
    from pathlib import Path

    try:
        return str(Path(path).resolve().relative_to(CONFIG.paths.repo_root))
    except ValueError:
        return path


def inject_styles() -> None:
    style = CONFIG.style
    mobile_root_tokens = _load_mobile_root_tokens()
    st.markdown(
        f"""
        <style>
            {mobile_root_tokens}
            .stApp {{
                background:
                    radial-gradient(circle at top left, rgba(94, 194, 255, 0.18), transparent 30%),
                    linear-gradient(180deg, {style.background} 0%, #050a13 100%);
                color: {style.text_primary};
            }}
            .block-container {{
                max-width: 1400px;
                padding-top: 1rem;
                padding-bottom: 4rem;
            }}
            [data-testid="stSidebar"] {{
                background:
                    radial-gradient(circle at top right, rgba(246, 80, 143, 0.18), transparent 28%),
                    linear-gradient(180deg, rgba(5, 10, 19, 0.98), rgba(8, 15, 26, 0.98));
                border-right: 1px solid rgba(255, 255, 255, 0.08);
            }}
            [data-testid="stSidebar"] * {{
                color: {style.text_primary};
            }}
            [data-testid="stSidebar"] .stSelectbox label,
            [data-testid="stSidebar"] .stToggle label {{
                color: {style.text_primary};
            }}
            [data-testid="stSidebar"] [data-baseweb="select"] > div,
            [data-testid="stSidebar"] [data-baseweb="select"] input {{
                background: rgba(255, 255, 255, 0.06);
                border-radius: 16px;
            }}
            [data-testid="stSidebar"] .st-emotion-cache-16txtl3,
            [data-testid="stSidebar"] .st-emotion-cache-1r6slb0 {{
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
            .dashboard-title-row {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 1.25rem;
                margin-bottom: 0.85rem;
            }}
            .dashboard-title-copy h1 {{
                margin: 0;
                font-size: clamp(2.05rem, 3vw, 3rem);
                line-height: 1.04;
                letter-spacing: -0.05em;
                color: {style.text_primary};
            }}
            .dashboard-score-pill {{
                display: inline-flex;
                align-items: center;
                gap: 0.85rem;
                padding: 0.7rem 0.95rem;
                border-radius: 26px;
                border: 1px solid rgba(255, 255, 255, 0.10);
                background:
                    linear-gradient(180deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.03)),
                    rgba(15, 27, 45, 0.82);
                box-shadow: 0 22px 50px rgba(0, 0, 0, 0.18);
            }}
            .dashboard-score-avatar {{
                width: 52px;
                height: 52px;
                border-radius: 18px;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 1.05rem;
                font-weight: 760;
            }}
            .dashboard-score-avatar.selected {{
                background: linear-gradient(135deg, rgba(94, 194, 255, 1), rgba(68, 154, 255, 0.82));
            }}
            .dashboard-score-avatar.match {{
                background: linear-gradient(135deg, rgba(246, 80, 143, 1), rgba(255, 142, 101, 0.82));
            }}
            .dashboard-score-copy {{
                text-align: center;
                min-width: 88px;
            }}
            .dashboard-score-value {{
                margin: 0;
                font-size: 2.1rem;
                line-height: 1;
                font-weight: 800;
                letter-spacing: -0.05em;
                background: linear-gradient(90deg, rgba(246, 80, 143, 1), rgba(196, 181, 253, 0.98));
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }}
            .dashboard-score-label {{
                margin: 0.2rem 0 0 0;
                color: {style.text_muted};
                font-size: 0.86rem;
            }}
            .dashboard-divider {{
                height: 1px;
                margin: 0 0 1rem 0;
                background: linear-gradient(90deg, rgba(255, 255, 255, 0.12), rgba(255, 255, 255, 0.04));
            }}
            .dashboard-section-label {{
                margin: 0 0 1rem 0;
                color: {style.text_primary};
                font-size: clamp(1.18rem, 1.65vw, 1.72rem);
                line-height: 1.1;
                font-weight: 780;
                letter-spacing: -0.03em;
                text-transform: uppercase;
            }}
            @media (max-width: 900px) {{
                .hero-intro-heading {{
                    font-size: 1.25rem;
                }}
                .hero-intro-body {{
                    font-size: 0.96rem;
                }}
                .dashboard-title-row {{
                    flex-direction: column;
                    align-items: flex-start;
                }}
                .dashboard-score-pill {{
                    width: 100%;
                    justify-content: center;
                }}
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _load_mobile_root_tokens() -> str:
    from pathlib import Path

    style_path = Path(__file__).resolve().parents[1] / "mobile-demo" / "style.css"
    css = style_path.read_text(encoding="utf-8")
    match = re.search(r":root\s*\{.*?\}", css, flags=re.DOTALL)
    return match.group(0) if match else ""


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


def _initials(value: str) -> str:
    cleaned = " ".join(part for part in value.split() if part)
    if not cleaned:
        return "??"

    pieces = cleaned.split()
    if len(pieces) == 1:
        return pieces[0][:2].upper()
    return "".join(piece[0] for piece in pieces[:2]).upper()


def render_dashboard_header(context) -> None:
    st.markdown(
        """
        <div class="dashboard-title-row">
            <div class="dashboard-title-copy">
                <h1>Spotdate Implementation Ideas</h1>
            </div>
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

    render_dashboard_header(context)
    st.markdown('<div class="dashboard-divider"></div>', unsafe_allow_html=True)
    st.markdown(
        '<h2 class="dashboard-section-label">1. What would the user see?</h2>',
        unsafe_allow_html=True,
    )
    render_implementation_ideas_grid(context)
    st.markdown(
        '<h2 class="dashboard-section-label">2. What does the model see?</h2>',
        unsafe_allow_html=True,
    )
    render_model_explanation_section(context)


if __name__ == "__main__":
    main()
