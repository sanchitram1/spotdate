from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from html import escape
from pathlib import Path
import re

import streamlit.components.v1 as components


@dataclass(frozen=True)
class Screen:
    eyebrow: str
    title: str
    subtitle: str
    visual_html: str
    body: str = ""
    footer: str = ""


def render_phone_screens(
    *,
    concept_key: str,
    selected_alias: str,
    match_alias: str,
    match_score: float,
    screens: list[Screen],
    height: int = 860,
    phone_width: int = 390,
    compact: bool = False,
) -> None:
    screen_markup = "".join(
        _build_screen_markup(
            screen=screen,
            index=index,
            total=len(screens),
            selected_alias=selected_alias,
            match_alias=match_alias,
            match_score=match_score,
        )
        for index, screen in enumerate(screens)
    )
    component_id = _slugify(concept_key)
    compact_styles = _build_compact_phone_overrides() if compact else ""
    phone_shell_class = "phone-shell compact" if compact else "phone-shell"

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta
            name="viewport"
            content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"
        >
        <style>
            {_load_mobile_component_css()}
            body {{
                margin: 0;
                background: transparent;
                font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display",
                    "Segoe UI", sans-serif;
                overflow: hidden;
            }}

            #app {{
                width: 100%;
                height: {height}px;
                max-width: 100%;
                background: transparent;
                box-shadow: none;
                display: flex;
                align-items: center;
                justify-content: center;
            }}

            .phone-shell {{
                width: {phone_width}px;
                max-width: calc(100vw - 24px);
                height: {height - 20}px;
                padding: 14px;
                border-radius: 44px;
                background:
                    linear-gradient(180deg, rgba(255, 255, 255, 0.22), rgba(255, 255, 255, 0.05)),
                    rgba(8, 15, 26, 0.72);
                box-shadow:
                    0 28px 90px rgba(0, 0, 0, 0.42),
                    inset 0 1px 0 rgba(255, 255, 255, 0.18);
            }}

            {compact_styles}

            .phone-bezel {{
                position: relative;
                height: 100%;
                border-radius: 34px;
                overflow: hidden;
                background:
                    radial-gradient(circle at top right, rgba(246, 80, 143, 0.18), transparent 34%),
                    radial-gradient(circle at top left, rgba(94, 194, 255, 0.18), transparent 36%),
                    linear-gradient(180deg, rgba(5, 10, 19, 0.98), rgba(8, 15, 26, 1));
                border: 1px solid rgba(255, 255, 255, 0.08);
                cursor: pointer;
                user-select: none;
            }}

            .phone-bezel::before {{
                content: "";
                position: absolute;
                inset: 0;
                background:
                    radial-gradient(circle at 50% 0%, rgba(255, 255, 255, 0.07), transparent 28%);
                pointer-events: none;
            }}

            .phone-notch {{
                position: absolute;
                top: 14px;
                left: 50%;
                transform: translateX(-50%);
                width: 128px;
                height: 28px;
                border-radius: 999px;
                background: rgba(0, 0, 0, 0.72);
                border: 1px solid rgba(255, 255, 255, 0.04);
                z-index: 5;
            }}

            .phone-status {{
                position: absolute;
                inset: 0 20px auto 20px;
                top: 18px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                color: rgba(248, 250, 252, 0.92);
                font-size: 0.78rem;
                font-weight: 600;
                letter-spacing: 0.03em;
                z-index: 4;
            }}

            .status-icons {{
                display: flex;
                align-items: center;
                gap: 8px;
            }}

            .battery {{
                width: 24px;
                height: 12px;
                border: 1px solid rgba(255, 255, 255, 0.72);
                border-radius: 4px;
                position: relative;
            }}

            .battery::before {{
                content: "";
                position: absolute;
                inset: 2px;
                border-radius: 2px;
                background: linear-gradient(90deg, var(--accent-green), #90f3d1);
            }}

            .battery::after {{
                content: "";
                position: absolute;
                right: -3px;
                top: 3px;
                width: 2px;
                height: 4px;
                border-radius: 1px;
                background: rgba(255, 255, 255, 0.72);
            }}

            .screen-track {{
                position: absolute;
                inset: 64px 0 0 0;
            }}

            .tap-screen {{
                position: absolute;
                inset: 0;
                padding: 22px 22px 28px;
                display: flex;
                flex-direction: column;
                gap: 10px;
                opacity: 0;
                transform: translateX(18px);
                transition:
                    opacity 240ms ease,
                    transform 240ms ease;
                pointer-events: none;
            }}

            .tap-screen.active {{
                opacity: 1;
                transform: translateX(0);
            }}

            .screen-top-half,
            .screen-bottom-half {{
                border-radius: 0;
                border: 0;
                background: transparent;
                backdrop-filter: none;
                -webkit-backdrop-filter: none;
            }}

            .screen-top-half {{
                min-height: 206px;
                padding: 8px 4px 10px;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
            }}

            .match-image-placeholder {{
                width: 126px;
                height: 126px;
                margin: 0 auto;
                border-radius: 28px;
                border: 1px solid rgba(255, 255, 255, 0.14);
                background: rgba(255, 255, 255, 0.06);
                display: grid;
                place-items: center;
                text-transform: lowercase;
                color: rgba(248, 250, 252, 0.7);
                font-size: 0.9rem;
                letter-spacing: 0.03em;
            }}

            .top-half-meta {{
                display: flex;
                justify-content: space-between;
                align-items: baseline;
                gap: 12px;
                border-top: 0;
                padding-top: 10px;
            }}

            .top-half-match {{
                color: white;
                font-size: 1.12rem;
                font-weight: 730;
                line-height: 1.15;
            }}

            .top-half-score {{
                color: white;
                font-size: 1.42rem;
                font-weight: 780;
                letter-spacing: -0.02em;
            }}

            .screen-bottom-half {{
                flex: 1;
                min-height: 0;
                padding: 12px 4px 8px;
                display: flex;
                flex-direction: column;
                gap: 10px;
            }}

            .visual-card {{
                flex: 1;
                min-height: 0;
                border-radius: 0;
                padding: 8px 0;
                background: transparent;
                border: 0;
                display: flex;
                flex-direction: column;
                justify-content: flex-start;
                gap: 10px;
            }}

            .screen-body,
            .screen-footer {{
                color: rgba(248, 250, 252, 0.82);
                font-size: 0.88rem;
                line-height: 1.48;
            }}

            .screen-footer {{
                color: var(--text-muted);
            }}

            .screen-dots {{
                display: flex;
                justify-content: center;
                gap: 8px;
                margin-top: 4px;
            }}

            .screen-dot {{
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.18);
                transition:
                    transform 180ms ease,
                    background 180ms ease;
            }}

            .screen-dot.active {{
                background: linear-gradient(135deg, var(--accent-red), var(--accent-blue));
                transform: scale(1.18);
            }}

            .spotlight-card {{
                padding: 18px;
                border-radius: 24px;
                background:
                    linear-gradient(135deg, rgba(246, 80, 143, 0.18), rgba(94, 194, 255, 0.14)),
                    rgba(8, 17, 31, 0.82);
                border: 1px solid rgba(255, 255, 255, 0.09);
            }}

            .spotlight-kicker,
            .metric-label,
            .legend-meta,
            .viz-label {{
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-size: 0.7rem;
                color: var(--text-muted);
            }}

            .spotlight-title {{
                font-size: 1.55rem;
                line-height: 1.08;
                color: white;
                font-weight: 750;
                margin-top: 10px;
            }}

            .spotlight-subtitle {{
                color: rgba(248, 250, 252, 0.72);
                margin-top: 4px;
                font-size: 0.92rem;
            }}

            .metric-grid,
            .pill-stack,
            .legend-list,
            .insight-list {{
                display: flex;
                flex-direction: column;
                gap: 10px;
            }}

            .metric-row,
            .legend-row,
            .insight-row {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 12px;
                padding: 12px 14px;
                border-radius: 18px;
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.06);
            }}

            .metric-row strong,
            .legend-row strong,
            .insight-row strong {{
                color: white;
                font-size: 0.9rem;
            }}

            .metric-value,
            .legend-value {{
                color: white;
                font-weight: 700;
            }}

            .stats-panel {{
                display: flex;
                flex-direction: column;
                gap: 10px;
                height: 100%;
            }}

            .stats-header {{
                color: white;
                font-size: 1.2rem;
                line-height: 1.1;
                font-weight: 500;
                letter-spacing: -0.02em;
                text-align: center;
            }}

            .stats-subheader {{
                color: rgba(248, 250, 252, 0.68);
                font-size: 0.76rem;
            }}

            .stats-rows {{
                display: flex;
                flex-direction: column;
                gap: 12px;
                flex: 1;
                justify-content: center;
            }}

            .stats-row {{
                display: grid;
                grid-template-columns: minmax(0, 1fr);
                align-items: center;
                gap: 0;
                padding: 6px 0;
                border-radius: 0;
                background: transparent;
                border: 0;
            }}

            .stats-bar-track {{
                width: 100%;
                height: 35px;
                border-radius: 11px;
                background: transparent;
                overflow: hidden;
                display: flex;
                align-items: stretch;
            }}

            .stats-bar-fill {{
                height: 100%;
                border-radius: inherit;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 0.92rem;
                font-weight: 400;
                min-width: 0;
                white-space: nowrap;
            }}

            .stats-bar-fill.has-value {{
                min-width: 40px;
            }}

            .stats-bar-fill.selected {{
                background: #333333;
            }}

            .stats-bar-fill.match {{
                background: linear-gradient(90deg, rgba(246, 80, 143, 1), rgba(255, 142, 101, 0.84));
            }}

            .duo-columns {{
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 12px;
                align-items: end;
                min-height: 210px;
            }}

            .foundation-column {{
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 12px;
            }}

            .foundation-bar {{
                width: 100%;
                height: 168px;
                border-radius: 22px;
                padding: 12px;
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.06);
                display: flex;
                align-items: end;
            }}

            .foundation-fill {{
                width: 100%;
                border-radius: 16px;
                min-height: 18px;
                box-shadow: 0 10px 20px rgba(0, 0, 0, 0.18);
            }}

            .foundation-fill.selected {{
                background: linear-gradient(180deg, rgba(94, 194, 255, 0.95), rgba(62, 120, 255, 0.68));
            }}

            .foundation-fill.match {{
                background: linear-gradient(180deg, rgba(246, 80, 143, 0.95), rgba(255, 142, 101, 0.68));
            }}

            .foundation-share {{
                color: white;
                font-size: 1.18rem;
                font-weight: 750;
            }}

            .immersion-grid {{
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 12px;
            }}

            .immersion-card {{
                padding: 16px;
                border-radius: 22px;
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.06);
            }}

            .immersion-value {{
                font-size: 1.6rem;
                line-height: 1.1;
                font-weight: 760;
                color: white;
                margin-top: 8px;
            }}

            .immersion-track {{
                width: 100%;
                height: 10px;
                border-radius: 999px;
                background: rgba(255, 255, 255, 0.08);
                overflow: hidden;
            }}

            .immersion-fill {{
                height: 100%;
                border-radius: inherit;
            }}

            .immersion-fill.selected {{
                background: linear-gradient(90deg, rgba(94, 194, 255, 1), rgba(68, 154, 255, 0.82));
            }}

            .immersion-fill.match {{
                background: linear-gradient(90deg, rgba(246, 80, 143, 1), rgba(255, 142, 101, 0.82));
            }}

            .match-reveal {{
                display: flex;
                flex-direction: column;
                gap: 12px;
                align-items: stretch;
            }}

            .reveal-hero {{
                padding: 22px;
                border-radius: 28px;
                background:
                    radial-gradient(circle at top right, rgba(246, 80, 143, 0.18), transparent 32%),
                    linear-gradient(180deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.03)),
                    rgba(8, 17, 31, 0.82);
                border: 1px solid rgba(255, 255, 255, 0.08);
                text-align: center;
            }}

            .reveal-score {{
                font-size: 2.3rem;
                font-weight: 800;
                line-height: 1;
                background: linear-gradient(90deg, var(--accent-red), var(--accent-blue));
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin: 12px 0 8px;
            }}

            .tag-cloud {{
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
            }}

            .tag-card {{
                flex: 1 1 100%;
                padding: 14px 16px;
                border-radius: 18px;
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.06);
                color: rgba(248, 250, 252, 0.88);
                line-height: 1.35;
                font-size: 0.88rem;
            }}

            .tag-card.good {{
                background: linear-gradient(135deg, rgba(77, 215, 168, 0.16), rgba(255, 255, 255, 0.04));
            }}

            .tag-card.quirk {{
                background: linear-gradient(135deg, rgba(246, 80, 143, 0.14), rgba(94, 194, 255, 0.08));
            }}

            .viz-stage {{
                display: flex;
                flex-direction: column;
                gap: 12px;
                align-items: center;
            }}

            .viz-stage svg {{
                width: 100%;
                max-width: 260px;
                height: auto;
                overflow: visible;
            }}

            .viz-legend {{
                width: 100%;
            }}

            .legend-dot {{
                width: 10px;
                height: 10px;
                border-radius: 50%;
                flex: 0 0 auto;
            }}

            .legend-copy {{
                display: flex;
                flex-direction: column;
                gap: 3px;
            }}

            .donut-wrap {{
                position: relative;
                width: 190px;
                height: 190px;
                border-radius: 50%;
                display: grid;
                place-items: center;
                margin: 0 auto;
            }}

            .donut-hole {{
                width: 112px;
                height: 112px;
                border-radius: 50%;
                background: rgba(5, 10, 19, 0.96);
                border: 1px solid rgba(255, 255, 255, 0.06);
                display: grid;
                place-items: center;
                text-align: center;
                color: white;
                box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
            }}

            .donut-hole strong {{
                display: block;
                font-size: 1.35rem;
                letter-spacing: -0.03em;
            }}

            .opposites-stack {{
                display: flex;
                flex-direction: column;
                gap: 12px;
            }}

            .opposite-row {{
                padding: 12px 14px;
                border-radius: 18px;
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.06);
            }}

            .opposite-label {{
                color: white;
                font-size: 0.88rem;
                font-weight: 650;
                margin-bottom: 10px;
            }}

            .opposite-track {{
                position: relative;
                height: 6px;
                border-radius: 999px;
                background: rgba(255, 255, 255, 0.08);
            }}

            .opposite-span {{
                position: absolute;
                top: 0;
                height: 100%;
                border-radius: inherit;
                background: rgba(255, 255, 255, 0.18);
            }}

            .opposite-point {{
                position: absolute;
                top: 50%;
                width: 14px;
                height: 14px;
                border-radius: 50%;
                transform: translate(-50%, -50%);
                box-shadow: 0 0 0 4px rgba(5, 10, 19, 0.96);
            }}

            .opposite-point.selected {{
                background: var(--accent-blue);
                box-shadow:
                    0 0 0 4px rgba(5, 10, 19, 0.96),
                    0 0 14px rgba(94, 194, 255, 0.45);
            }}

            .opposite-point.match {{
                background: var(--accent-red);
                box-shadow:
                    0 0 0 4px rgba(5, 10, 19, 0.96),
                    0 0 14px rgba(246, 80, 143, 0.45);
            }}

            .opposite-meta {{
                display: flex;
                justify-content: space-between;
                margin-top: 10px;
                color: var(--text-muted);
                font-size: 0.72rem;
            }}

            @media (max-width: 460px) {{
                #app {{
                    height: {height - 40}px;
                }}

                .phone-shell {{
                    width: 100%;
                    height: {height - 60}px;
                    padding: 10px;
                }}

                .tap-screen {{
                    padding: 18px 18px 22px;
                    gap: 14px;
                }}

                .pair-card {{
                    padding: 14px;
                }}

                .profile-avatar {{
                    width: 52px;
                    height: 52px;
                }}

                .screen-title {{
                    font-size: 1.48rem;
                }}

                .screen-subtitle,
                .screen-body,
                .screen-footer {{
                    font-size: 0.82rem;
                    line-height: 1.4;
                }}

                .visual-card {{
                    padding: 14px;
                    border-radius: 24px;
                }}

                .spotlight-title,
                .immersion-value {{
                    font-size: 1.34rem;
                }}
            }}
        </style>
    </head>
    <body>
        <div id="app">
            <div class="{phone_shell_class}">
                <div class="phone-bezel" id="{component_id}">
                    <div class="phone-notch"></div>
                    <div class="phone-status">
                        <span>9:41</span>
                        <div class="status-icons">
                            <span>5G</span>
                            <div class="battery"></div>
                        </div>
                    </div>
                    <div class="screen-track">
                        {screen_markup}
                    </div>
                </div>
            </div>
        </div>
        <script>
            (() => {{
                const root = document.getElementById({component_id!r});
                if (!root) {{
                    return;
                }}

                const screens = Array.from(root.querySelectorAll('.tap-screen'));
                let index = 0;

                const paint = (nextIndex) => {{
                    index = nextIndex % screens.length;
                    screens.forEach((screen, screenIndex) => {{
                        screen.classList.toggle('active', screenIndex === index);
                    }});
                    screens.forEach((screen) => {{
                        const dots = Array.from(screen.querySelectorAll('.screen-dot'));
                        dots.forEach((dot, dotIndex) => {{
                            dot.classList.toggle('active', dotIndex === index);
                        }});
                    }});
                }};

                root.addEventListener('click', () => paint(index + 1));
                paint(0);
            }})();
        </script>
    </body>
    </html>
    """

    components.html(html, height=height, scrolling=False)


def render_phone_concept_card(
    *,
    concept_key: str,
    card_label: str,
    card_description: str,
    selected_alias: str,
    match_alias: str,
    match_score: float,
    screens: list[Screen],
    height: int = 940,
    phone_height: int = 740,
    phone_width: int = 308,
) -> None:
    screen_markup = "".join(
        _build_screen_markup(
            screen=screen,
            index=index,
            total=len(screens),
            selected_alias=selected_alias,
            match_alias=match_alias,
            match_score=match_score,
        )
        for index, screen in enumerate(screens)
    )
    component_id = _slugify(concept_key)
    safe_card_label = escape(card_label)
    safe_card_description = escape(card_description)

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta
            name="viewport"
            content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"
        >
        <style>
            {_load_mobile_component_css()}
            body {{
                margin: 0;
                background: transparent;
                font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display",
                    "Segoe UI", sans-serif;
                overflow: hidden;
            }}

            #app {{
                width: 100%;
                height: {height}px;
                max-width: 100%;
            }}

            .concept-card-shell {{
                height: 100%;
                display: flex;
                flex-direction: column;
                overflow: hidden;
                border-radius: 28px;
                border: 1px solid rgba(255, 255, 255, 0.10);
                background:
                    radial-gradient(circle at top left, rgba(94, 194, 255, 0.10), transparent 28%),
                    radial-gradient(circle at top right, rgba(246, 80, 143, 0.10), transparent 34%),
                    linear-gradient(180deg, rgba(22, 31, 49, 0.98), rgba(11, 18, 31, 0.98));
                box-shadow:
                    0 32px 80px rgba(0, 0, 0, 0.24),
                    inset 0 1px 0 rgba(255, 255, 255, 0.06);
            }}

            .concept-card-head {{
                min-height: 116px;
                padding: 1rem 1.05rem 0.95rem;
                border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            }}

            .concept-card-kicker {{
                margin: 0;
                color: rgba(248, 250, 252, 0.96);
                font-size: 1rem;
                font-weight: 760;
                line-height: 1.35;
                text-transform: uppercase;
            }}

            .concept-card-description {{
                margin: 0.45rem 0 0;
                color: rgba(248, 250, 252, 0.78);
                font-size: 0.86rem;
                line-height: 1.45;
            }}

            .concept-card-stage {{
                flex: 1;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 1rem 0.65rem;
                background:
                    radial-gradient(circle at center, rgba(255, 255, 255, 0.02), transparent 52%),
                    linear-gradient(180deg, rgba(255, 255, 255, 0.02), rgba(255, 255, 255, 0.00));
            }}

            .phone-shell {{
                width: {phone_width}px;
                max-width: 100%;
                height: {phone_height}px;
                padding: 12px;
                border-radius: 40px;
                background:
                    linear-gradient(180deg, rgba(255, 255, 255, 0.22), rgba(255, 255, 255, 0.05)),
                    rgba(8, 15, 26, 0.76);
                box-shadow:
                    0 26px 82px rgba(0, 0, 0, 0.44),
                    inset 0 1px 0 rgba(255, 255, 255, 0.18);
            }}

            {_build_compact_phone_overrides()}

            .phone-bezel {{
                position: relative;
                height: 100%;
                border-radius: 31px;
                overflow: hidden;
                background:
                    radial-gradient(circle at top right, rgba(246, 80, 143, 0.18), transparent 34%),
                    radial-gradient(circle at top left, rgba(94, 194, 255, 0.18), transparent 36%),
                    linear-gradient(180deg, rgba(5, 10, 19, 0.98), rgba(8, 15, 26, 1));
                border: 1px solid rgba(255, 255, 255, 0.08);
                cursor: pointer;
                user-select: none;
            }}

            .phone-bezel::before {{
                content: "";
                position: absolute;
                inset: 0;
                background:
                    radial-gradient(circle at 50% 0%, rgba(255, 255, 255, 0.07), transparent 28%);
                pointer-events: none;
            }}

            .phone-notch {{
                position: absolute;
                top: 12px;
                left: 50%;
                transform: translateX(-50%);
                width: 104px;
                height: 24px;
                border-radius: 999px;
                background: rgba(0, 0, 0, 0.72);
                border: 1px solid rgba(255, 255, 255, 0.04);
                z-index: 5;
            }}

            .phone-status {{
                position: absolute;
                inset: 0 18px auto 18px;
                top: 16px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                color: rgba(248, 250, 252, 0.92);
                font-size: 0.74rem;
                font-weight: 600;
                letter-spacing: 0.03em;
                z-index: 4;
            }}

            .status-icons {{
                display: flex;
                align-items: center;
                gap: 8px;
            }}

            .battery {{
                width: 22px;
                height: 11px;
                border: 1px solid rgba(255, 255, 255, 0.72);
                border-radius: 4px;
                position: relative;
            }}

            .battery::before {{
                content: "";
                position: absolute;
                inset: 2px;
                border-radius: 2px;
                background: linear-gradient(90deg, var(--accent-green), #90f3d1);
            }}

            .battery::after {{
                content: "";
                position: absolute;
                right: -3px;
                top: 3px;
                width: 2px;
                height: 4px;
                border-radius: 1px;
                background: rgba(255, 255, 255, 0.72);
            }}

            .screen-track {{
                position: absolute;
                inset: 58px 0 0 0;
            }}

            .tap-screen {{
                position: absolute;
                inset: 0;
                padding: 18px 18px 22px;
                display: flex;
                flex-direction: column;
                gap: 10px;
                opacity: 0;
                transform: translateX(18px);
                transition:
                    opacity 240ms ease,
                    transform 240ms ease;
                pointer-events: none;
            }}

            .tap-screen.active {{
                opacity: 1;
                transform: translateX(0);
            }}

            .screen-top-half,
            .screen-bottom-half {{
                border-radius: 0;
                border: 0;
                background: transparent;
            }}

            .screen-top-half {{
                min-height: 182px;
                padding: 8px 4px 10px;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
            }}

            .match-image-placeholder {{
                width: 108px;
                height: 108px;
                margin: 0 auto;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.14);
                background: rgba(255, 255, 255, 0.06);
                display: grid;
                place-items: center;
                text-transform: lowercase;
                color: rgba(248, 250, 252, 0.7);
                font-size: 0.82rem;
                letter-spacing: 0.03em;
            }}

            .top-half-meta {{
                display: flex;
                justify-content: space-between;
                align-items: baseline;
                gap: 10px;
                border-top: 0;
                padding-top: 9px;
            }}

            .top-half-match {{
                color: white;
                font-size: 1rem;
                font-weight: 720;
            }}

            .top-half-score {{
                color: white;
                font-size: 1.3rem;
                font-weight: 780;
                letter-spacing: -0.02em;
            }}

            .screen-bottom-half {{
                flex: 1;
                min-height: 0;
                padding: 12px 4px 8px;
                display: flex;
                flex-direction: column;
                gap: 9px;
            }}

            .visual-card {{
                flex: 1;
                min-height: 0;
                border-radius: 0;
                padding: 6px 0;
                background: transparent;
                border: 0;
                display: flex;
                flex-direction: column;
                justify-content: flex-start;
                gap: 9px;
            }}

            .screen-body,
            .screen-footer {{
                color: rgba(248, 250, 252, 0.82);
                font-size: 0.8rem;
                line-height: 1.42;
            }}

            .screen-footer {{
                color: var(--text-muted);
            }}

            .stats-panel {{
                display: flex;
                flex-direction: column;
                gap: 10px;
                height: 100%;
            }}

            .stats-header {{
                color: white;
                font-size: 1.04rem;
                line-height: 1.12;
                font-weight: 500;
                letter-spacing: -0.02em;
                text-align: center;
            }}

            .stats-subheader {{
                color: rgba(248, 250, 252, 0.68);
                font-size: 0.7rem;
            }}

            .stats-rows {{
                display: flex;
                flex-direction: column;
                gap: 12px;
                flex: 1;
                justify-content: center;
            }}

            .stats-row {{
                display: grid;
                grid-template-columns: minmax(0, 1fr);
                align-items: center;
                gap: 0;
                padding: 5px 0;
                border-radius: 0;
                background: transparent;
                border: 0;
            }}

            .stats-bar-track {{
                width: 100%;
                height: 29px;
                border-radius: 10px;
                background: transparent;
                overflow: hidden;
                display: flex;
                align-items: stretch;
            }}

            .stats-bar-fill {{
                height: 100%;
                border-radius: inherit;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 0.84rem;
                font-weight: 400;
                min-width: 0;
                white-space: nowrap;
            }}

            .stats-bar-fill.has-value {{
                min-width: 34px;
            }}

            .stats-bar-fill.selected {{
                background: #333333;
            }}

            .stats-bar-fill.match {{
                background: linear-gradient(90deg, rgba(246, 80, 143, 1), rgba(255, 142, 101, 0.84));
            }}

            .screen-dots {{
                display: flex;
                justify-content: center;
                gap: 7px;
                margin-top: 2px;
            }}

            .screen-dot {{
                width: 7px;
                height: 7px;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.18);
                transition:
                    transform 180ms ease,
                    background 180ms ease;
            }}

            .screen-dot.active {{
                background: linear-gradient(135deg, var(--accent-red), var(--accent-blue));
                transform: scale(1.16);
            }}
        </style>
    </head>
    <body>
        <div id="app">
            <section class="concept-card-shell">
                <div class="concept-card-head">
                    <p class="concept-card-kicker">{safe_card_label}</p>
                    <p class="concept-card-description">{safe_card_description}</p>
                </div>
                <div class="concept-card-stage">
                    <div class="phone-shell compact">
                        <div class="phone-bezel" id="{component_id}">
                            <div class="phone-notch"></div>
                            <div class="phone-status">
                                <span>9:41</span>
                                <div class="status-icons">
                                    <span>5G</span>
                                    <div class="battery"></div>
                                </div>
                            </div>
                            <div class="screen-track">
                                {screen_markup}
                            </div>
                        </div>
                    </div>
                </div>
            </section>
        </div>
        <script>
            (() => {{
                const root = document.getElementById({component_id!r});
                if (!root) {{
                    return;
                }}

                const screens = Array.from(root.querySelectorAll('.tap-screen'));
                let index = 0;

                const paint = (nextIndex) => {{
                    index = nextIndex % screens.length;
                    screens.forEach((screen, screenIndex) => {{
                        screen.classList.toggle('active', screenIndex === index);
                    }});
                    screens.forEach((screen) => {{
                        const dots = Array.from(screen.querySelectorAll('.screen-dot'));
                        dots.forEach((dot, dotIndex) => {{
                            dot.classList.toggle('active', dotIndex === index);
                        }});
                    }});
                }};

                root.addEventListener('click', () => paint(index + 1));
                paint(0);
            }})();
        </script>
    </body>
    </html>
    """

    components.html(html, height=height, scrolling=False)


def _build_screen_markup(
    *,
    screen: Screen,
    index: int,
    total: int,
    selected_alias: str,
    match_alias: str,
    match_score: float,
) -> str:
    safe_body = escape(screen.body)
    safe_footer = escape(screen.footer)
    safe_match_alias = escape(match_alias)
    safe_score = f"{max(0.0, min(1.0, match_score)):.0%}"
    body_markup = f'<div class="screen-body">{safe_body}</div>' if safe_body else ""
    footer_markup = (
        f'<div class="screen-footer">{safe_footer}</div>' if safe_footer else ""
    )

    return f"""
    <section class="tap-screen{" active" if index == 0 else ""}">
        <div class="screen-top-half">
            <div class="match-image-placeholder">placeholder</div>
            <div class="top-half-meta">
                <span class="top-half-match">{safe_match_alias}</span>
                <span class="top-half-score">{safe_score}</span>
            </div>
        </div>
        <div class="screen-bottom-half">
            <div class="visual-card">
                {screen.visual_html}
            </div>
            {body_markup}
            {footer_markup}
        </div>
        <div class="screen-dots">
            {"".join(f'<span class="screen-dot{" active" if dot_index == index == 0 else ""}"></span>' for dot_index in range(total))}
        </div>
    </section>
    """


def _build_compact_phone_overrides() -> str:
    return """
        .phone-shell.compact {
            --phone-body-copy: 0.82rem;
        }

        .phone-shell.compact .screen-top-half {
            min-height: 168px;
            padding: 10px 10px 9px;
            border-radius: 0;
        }

        .phone-shell.compact .match-image-placeholder {
            width: 94px;
            height: 94px;
            border-radius: 18px;
            font-size: 0.76rem;
        }

        .phone-shell.compact .top-half-match {
            font-size: 0.92rem;
        }

        .phone-shell.compact .top-half-score {
            font-size: 1.2rem;
        }

        .phone-shell.compact .screen-bottom-half {
            padding: 10px;
            border-radius: 0;
        }

        .phone-shell.compact .stats-header {
            font-size: 1.14rem;
        }

        .phone-shell.compact .stats-subheader {
            font-size: 0.72rem;
        }

        .phone-shell.compact .stats-row {
            padding: 8px;
            border-radius: 14px;
            gap: 8px;
        }

        .phone-shell.compact .stats-bar-track {
            height: 30px;
        }

        .phone-shell.compact .stats-bar-fill {
            font-size: 0.9rem;
        }

        .phone-shell.compact .pair-card {
            padding: 14px;
            border-radius: 22px;
        }

        .phone-shell.compact .profile-pill {
            min-width: 70px;
            gap: 6px;
        }

        .phone-shell.compact .profile-avatar {
            width: 48px;
            height: 48px;
            border-radius: 16px;
            font-size: 0.88rem;
        }

        .phone-shell.compact .profile-label {
            max-width: 74px;
            font-size: 0.67rem;
        }

        .phone-shell.compact .score-chip {
            padding: 9px 12px;
            border-radius: 18px;
        }

        .phone-shell.compact .score-chip strong {
            font-size: 1.1rem;
            margin-bottom: 3px;
        }

        .phone-shell.compact .score-chip span {
            font-size: 0.68rem;
        }

        .phone-shell.compact .screen-title {
            font-size: 1.42rem;
        }

        .phone-shell.compact .screen-subtitle {
            font-size: 0.82rem;
            line-height: 1.38;
        }

        .phone-shell.compact .screen-body,
        .phone-shell.compact .screen-footer {
            font-size: var(--phone-body-copy);
            line-height: 1.42;
        }

        .phone-shell.compact .visual-card {
            padding: 14px;
            border-radius: 24px;
            gap: 12px;
        }

        .phone-shell.compact .spotlight-card {
            padding: 14px;
            border-radius: 20px;
        }

        .phone-shell.compact .spotlight-title,
        .phone-shell.compact .immersion-value {
            font-size: 1.24rem;
        }

        .phone-shell.compact .spotlight-subtitle {
            font-size: 0.82rem;
        }

        .phone-shell.compact .metric-row,
        .phone-shell.compact .legend-row,
        .phone-shell.compact .insight-row {
            padding: 10px 12px;
            border-radius: 16px;
        }

        .phone-shell.compact .foundation-bar {
            height: 132px;
            border-radius: 18px;
        }

        .phone-shell.compact .duo-columns {
            min-height: 168px;
        }

        .phone-shell.compact .donut-wrap {
            width: 156px;
            height: 156px;
        }

        .phone-shell.compact .donut-hole {
            width: 92px;
            height: 92px;
        }

        .phone-shell.compact .donut-hole strong {
            font-size: 1.08rem;
        }

        .phone-shell.compact .viz-stage svg {
            max-width: 214px;
        }

        .phone-shell.compact .legend-copy strong {
            font-size: 0.8rem;
        }

        .phone-shell.compact .legend-meta,
        .phone-shell.compact .metric-label,
        .phone-shell.compact .viz-label {
            font-size: 0.63rem;
        }

        .phone-shell.compact .tag-card {
            padding: 12px 14px;
            font-size: 0.8rem;
        }

        .phone-shell.compact .reveal-score {
            font-size: 1.9rem;
        }
    """


@lru_cache(maxsize=1)
def _load_mobile_component_css() -> str:
    style_path = Path(__file__).resolve().parents[2] / "mobile-demo" / "style.css"
    return style_path.read_text(encoding="utf-8")


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return normalized or "screen-stack"


def _initials(label: str) -> str:
    parts = [part for part in re.split(r"[^A-Za-z0-9]+", label) if part]
    if not parts:
        return "SD"
    return "".join(part[0] for part in parts[:2]).upper()
