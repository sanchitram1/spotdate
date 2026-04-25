from __future__ import annotations

import csv
import math
import re
from dataclasses import dataclass
from functools import lru_cache
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

from dashboard.components.screen import Screen, render_phone_concept_card

# Legacy import preserved for reference during the redesign.
# from dashboard.components.screen import render_phone_screens
from dashboard.config import CONFIG, DashboardConfig
from dashboard.ideas.match_dna import MatchDNAIdea
from dashboard.ideas.new_radar import NewRadarIdea
from dashboard.ideas.opposites import OppositesIdea
from dashboard.ideas.quirks import QuirksIdea
from dashboard.types import PairContext

# Legacy imports preserved for reference during the dashboard redesign.
# from dashboard.ideas.registry import get_implementation_ideas


@dataclass(frozen=True)
class PairHistorySnapshot:
    shared_track_name: str | None
    shared_track_artist: str | None
    shared_track_selected_count: int
    shared_track_match_count: int
    shared_artist_name: str | None
    shared_genre_name: str | None
    shared_genre_selected_share: float
    shared_genre_match_share: float
    selected_minutes: int
    match_minutes: int
    selected_total_listens: int
    match_total_listens: int


@dataclass(frozen=True)
class ConceptCardSpec:
    concept_key: str
    card_label: str
    card_description: str
    screens: list[Screen]
    height: int
    phone_height: int
    phone_width: int


@lru_cache(maxsize=1)
def _load_mobile_root_tokens() -> str:
    style_path = Path(__file__).resolve().parents[2] / "mobile-demo" / "style.css"
    css = style_path.read_text(encoding="utf-8")
    match = re.search(r":root\s*\{.*?\}", css, flags=re.DOTALL)
    if match:
        return match.group(0)
    return """
    :root {
        --bg-color: #050a13;
        --text-primary: #f8fafc;
        --text-muted: #94a3b8;
        --accent-red: rgba(246, 80, 143, 1);
        --accent-blue: #5ec2ff;
        --accent-green: #4dd7a8;
        --card-bg: rgba(15, 27, 45, 0.6);
        --card-border: rgba(255, 255, 255, 0.08);
    }
    """


def _inject_showcase_styles() -> None:
    st.markdown(
        f"""
        <style>
            {_load_mobile_root_tokens()}

            .block-container {{
                max-width: 1400px;
                padding-top: 1.25rem;
                padding-bottom: 4rem;
            }}

            .concept-header,
            .model-lens-shell,
            .lens-card {{
                border: 1px solid rgba(255, 255, 255, 0.08);
                background:
                    linear-gradient(180deg, rgba(255, 255, 255, 0.06), rgba(255, 255, 255, 0.03)),
                    rgba(15, 27, 45, 0.74);
                backdrop-filter: blur(18px);
                -webkit-backdrop-filter: blur(18px);
                box-shadow: 0 20px 50px rgba(0, 0, 0, 0.16);
            }}

            .concept-header,
            .model-lens-shell {{
                border-radius: 28px;
                padding: 1.45rem 1.55rem;
            }}

            .concept-header {{
                text-align: center;
                margin: 0 auto 1rem;
                max-width: 680px;
            }}

            .concept-kicker {{
                margin: 0 0 0.45rem 0;
                text-transform: uppercase;
                letter-spacing: 0.12em;
                font-size: 0.74rem;
                font-weight: 700;
                color: var(--accent-blue);
            }}

            .concept-title {{
                margin: 0;
                font-size: 2rem;
                line-height: 1.02;
                letter-spacing: -0.04em;
                color: var(--text-primary);
            }}

            .concept-summary {{
                margin: 0.65rem auto 0;
                max-width: 52ch;
                color: rgba(248, 250, 252, 0.74);
                line-height: 1.6;
                font-size: 0.98rem;
            }}

            .concept-gap {{
                height: 1.5rem;
            }}

            .model-lens-shell {{
                margin-top: 0.75rem;
            }}

            .lens-grid {{
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 14px;
                margin-top: 1rem;
            }}

            .lens-card {{
                border-radius: 22px;
                padding: 1rem 1.05rem;
            }}

            .lens-kicker {{
                margin: 0 0 0.45rem 0;
                text-transform: uppercase;
                letter-spacing: 0.09em;
                font-size: 0.72rem;
                color: var(--accent-green);
            }}

            .lens-card h3 {{
                margin: 0 0 0.45rem 0;
                color: var(--text-primary);
                font-size: 1.02rem;
            }}

            .lens-card p {{
                margin: 0;
                color: rgba(248, 250, 252, 0.72);
                line-height: 1.55;
                font-size: 0.92rem;
            }}

            .lens-chip-row {{
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                margin-top: 1rem;
            }}

            .lens-chip {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                padding: 0.52rem 0.82rem;
                border-radius: 999px;
                background: rgba(255, 255, 255, 0.07);
                border: 1px solid rgba(255, 255, 255, 0.08);
                color: var(--text-primary);
                font-size: 0.84rem;
            }}

            .showcase-section-title {{
                margin: 0 0 1.1rem 0;
                font-size: 1.65rem;
                line-height: 1.05;
                letter-spacing: -0.03em;
                text-transform: uppercase;
                color: var(--text-primary);
            }}

            .showcase-columns {{
                margin-top: 1rem;
            }}

            .showcase-card-head,
            .showcase-card-foot,
            .model-process-shell,
            .model-stage,
            .model-output-list,
            .model-summary-shell {{
                border: 1px solid rgba(255, 255, 255, 0.08);
                background:
                    linear-gradient(180deg, rgba(255, 255, 255, 0.06), rgba(255, 255, 255, 0.03)),
                    rgba(15, 27, 45, 0.74);
                box-shadow: 0 20px 50px rgba(0, 0, 0, 0.16);
                backdrop-filter: blur(18px);
                -webkit-backdrop-filter: blur(18px);
            }}

            .showcase-card-head,
            .showcase-card-foot,
            .model-process-shell,
            .model-summary-shell {{
                border-radius: 24px;
            }}

            .showcase-card-head {{
                padding: 1rem 1.05rem 0.95rem;
                min-height: 104px;
                margin-bottom: 0.65rem;
            }}

            .showcase-card-kicker {{
                margin: 0;
                font-size: 0.9rem;
                line-height: 1.35;
                font-weight: 760;
                color: var(--text-primary);
                text-transform: uppercase;
            }}

            .showcase-card-subkicker {{
                color: rgba(248, 250, 252, 0.72);
                font-weight: 500;
                text-transform: none;
            }}

            .showcase-card-foot {{
                margin-top: 0.7rem;
                padding: 1rem 1.05rem 1.05rem;
                min-height: 106px;
            }}

            .showcase-card-foot p {{
                margin: 0;
                color: rgba(248, 250, 252, 0.86);
                line-height: 1.5;
                font-size: 0.99rem;
            }}

            .showcase-card-foot strong {{
                color: var(--text-primary);
            }}

            .showcase-visual-tags {{
                display: flex;
                flex-wrap: wrap;
                gap: 0.45rem;
                margin-top: 0.8rem;
            }}

            .showcase-visual-tag {{
                display: inline-flex;
                align-items: center;
                padding: 0.36rem 0.65rem;
                border-radius: 999px;
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.08);
                color: rgba(248, 250, 252, 0.82);
                font-size: 0.78rem;
            }}

            .model-process-shell {{
                padding: 1rem 1.05rem 1.15rem;
                margin-top: 1rem;
            }}

            .model-process-grid {{
                display: grid;
                grid-template-columns: minmax(0, 1fr) 54px minmax(0, 1fr) 54px minmax(0, 1.2fr);
                gap: 16px;
                align-items: center;
                margin-top: 1rem;
            }}

            .model-stage {{
                border-radius: 22px;
                padding: 1.1rem 1rem;
                min-height: 210px;
            }}

            .model-stage-kicker {{
                margin: 0 0 0.7rem 0;
                font-size: 0.82rem;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                color: var(--text-muted);
            }}

            .model-stage-title {{
                margin: 0.65rem 0 0.55rem 0;
                font-size: 1.18rem;
                line-height: 1.15;
                color: var(--text-primary);
            }}

            .model-stage-body {{
                margin: 0;
                color: rgba(248, 250, 252, 0.72);
                line-height: 1.55;
                font-size: 0.92rem;
            }}

            .model-stage-icons,
            .model-avatar-row {{
                display: flex;
                align-items: center;
                gap: 0.65rem;
                flex-wrap: wrap;
            }}

            .model-icon-chip,
            .model-avatar-chip {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 52px;
                height: 52px;
                border-radius: 16px;
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.08);
                color: var(--text-primary);
                font-size: 1.45rem;
            }}

            .model-avatar-chip {{
                width: 46px;
                height: 46px;
                border-radius: 50%;
                font-size: 0.98rem;
                font-weight: 760;
            }}

            .model-avatar-chip.selected {{
                background: linear-gradient(135deg, rgba(94, 194, 255, 0.9), rgba(68, 154, 255, 0.72));
            }}

            .model-avatar-chip.match {{
                background: linear-gradient(135deg, rgba(246, 80, 143, 0.9), rgba(255, 142, 101, 0.72));
            }}

            .model-avatar-chip.neutral {{
                background: linear-gradient(135deg, rgba(196, 181, 253, 0.65), rgba(255, 255, 255, 0.18));
            }}

            .model-arrow {{
                display: flex;
                align-items: center;
                justify-content: center;
                color: rgba(248, 250, 252, 0.68);
                font-size: 2.2rem;
                line-height: 1;
            }}

            .model-output-list {{
                border-radius: 22px;
                padding: 1rem;
                display: flex;
                flex-direction: column;
                gap: 0.85rem;
                min-height: 210px;
            }}

            .model-output-row {{
                display: flex;
                align-items: flex-start;
                gap: 0.8rem;
                padding-bottom: 0.85rem;
                border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            }}

            .model-output-row:last-child {{
                padding-bottom: 0;
                border-bottom: 0;
            }}

            .model-output-icon {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 50px;
                height: 50px;
                border-radius: 16px;
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.08);
                font-size: 1.35rem;
            }}

            .model-output-title {{
                margin: 0 0 0.22rem 0;
                font-size: 1rem;
                line-height: 1.2;
                color: var(--text-primary);
                text-transform: uppercase;
            }}

            .model-output-body {{
                margin: 0;
                color: rgba(248, 250, 252, 0.72);
                line-height: 1.45;
                font-size: 0.92rem;
            }}

            .model-summary-shell {{
                margin-top: 1rem;
                padding: 0.95rem 1rem 1.05rem;
            }}

            .model-summary-shell p {{
                margin: 0;
                color: rgba(248, 250, 252, 0.88);
                line-height: 1.5;
                font-size: 1rem;
            }}

            .model-summary-shell strong {{
                color: var(--text-primary);
            }}

            @media (max-width: 900px) {{
                .concept-title {{
                    font-size: 1.7rem;
                }}

                .lens-grid {{
                    grid-template-columns: 1fr;
                }}

                .model-process-grid {{
                    grid-template-columns: 1fr;
                }}

                .model-arrow {{
                    transform: rotate(90deg);
                }}

                .showcase-card-head,
                .showcase-card-foot {{
                    min-height: unset;
                }}
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=3600)
def _compute_pair_history_snapshot(
    selected_user_id: str,
    match_user_id: str,
    artifact_root: str,
) -> PairHistorySnapshot | None:
    history_path = Path(artifact_root) / "data" / "past_listening_history.csv"
    if not history_path.exists():
        return None

    selected_tracks: dict[tuple[str, str], int] = {}
    match_tracks: dict[tuple[str, str], int] = {}
    selected_artists: dict[str, int] = {}
    match_artists: dict[str, int] = {}
    selected_genres: dict[str, int] = {}
    match_genres: dict[str, int] = {}
    selected_minutes = 0
    match_minutes = 0
    selected_total = 0
    match_total = 0

    def _parse_minutes(raw_value: str | None) -> int:
        if not raw_value:
            return 0
        try:
            return max(0, int(float(raw_value) / 60000))
        except ValueError:
            return 0

    with history_path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        for row in reader:
            user_id = row.get("user_id")
            if user_id == selected_user_id:
                selected_total += 1
                track_name = (row.get("track_name") or "").strip()
                artist_name = (row.get("artist_name") or "").strip()
                genre_name = (row.get("genre") or "").strip()

                if track_name:
                    selected_tracks[(track_name, artist_name)] = (
                        selected_tracks.get((track_name, artist_name), 0) + 1
                    )
                if artist_name:
                    selected_artists[artist_name] = (
                        selected_artists.get(artist_name, 0) + 1
                    )
                if genre_name:
                    selected_genres[genre_name] = selected_genres.get(genre_name, 0) + 1
                selected_minutes += _parse_minutes(row.get("duration_ms"))
            elif user_id == match_user_id:
                match_total += 1
                track_name = (row.get("track_name") or "").strip()
                artist_name = (row.get("artist_name") or "").strip()
                genre_name = (row.get("genre") or "").strip()

                if track_name:
                    match_tracks[(track_name, artist_name)] = (
                        match_tracks.get((track_name, artist_name), 0) + 1
                    )
                if artist_name:
                    match_artists[artist_name] = match_artists.get(artist_name, 0) + 1
                if genre_name:
                    match_genres[genre_name] = match_genres.get(genre_name, 0) + 1
                match_minutes += _parse_minutes(row.get("duration_ms"))

    if selected_total == 0 or match_total == 0:
        return None

    shared_tracks = sorted(
        set(selected_tracks).intersection(match_tracks),
        key=lambda item: selected_tracks[item] + match_tracks[item],
        reverse=True,
    )
    shared_artists = sorted(
        set(selected_artists).intersection(match_artists),
        key=lambda item: selected_artists[item] + match_artists[item],
        reverse=True,
    )
    shared_genres = sorted(
        set(selected_genres).intersection(match_genres),
        key=lambda item: selected_genres[item] + match_genres[item],
        reverse=True,
    )

    shared_track_name = None
    shared_track_artist = None
    shared_track_selected_count = 0
    shared_track_match_count = 0
    if shared_tracks:
        shared_track_name, shared_track_artist = shared_tracks[0]
        shared_track_selected_count = selected_tracks[shared_tracks[0]]
        shared_track_match_count = match_tracks[shared_tracks[0]]

    shared_genre_name = shared_genres[0] if shared_genres else None
    selected_genre_share = (
        selected_genres.get(shared_genre_name, 0) / selected_total
        if shared_genre_name
        else 0.0
    )
    match_genre_share = (
        match_genres.get(shared_genre_name, 0) / match_total
        if shared_genre_name
        else 0.0
    )

    return PairHistorySnapshot(
        shared_track_name=shared_track_name,
        shared_track_artist=shared_track_artist,
        shared_track_selected_count=shared_track_selected_count,
        shared_track_match_count=shared_track_match_count,
        shared_artist_name=shared_artists[0] if shared_artists else None,
        shared_genre_name=shared_genre_name,
        shared_genre_selected_share=selected_genre_share,
        shared_genre_match_share=match_genre_share,
        selected_minutes=selected_minutes,
        match_minutes=match_minutes,
        selected_total_listens=selected_total,
        match_total_listens=match_total,
    )


def _percent(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{max(0.0, min(1.0, float(value))):.0%}"


def _title_case(value: str | None, fallback: str) -> str:
    if not value:
        return fallback
    return value.replace("_", " ").title()


def _short_text(value: str, limit: int = 88) -> str:
    text = " ".join(str(value).split())
    if len(text) <= limit:
        return text
    return f"{text[: limit - 1].rstrip()}…"


def _short_axis_label(label: str) -> str:
    mapping = {
        "Night Listening": "Night",
        "Genre Breadth": "Range",
        "Artist Exploration": "Discovery",
        "Underground Lean": "Deep Cuts",
    }
    if label in mapping:
        return mapping[label]
    if len(label) <= 12:
        return label
    return label.replace("Listening", "").strip()[:12]


def _format_hours(minutes: int) -> str:
    if minutes <= 0:
        return "—"
    hours = minutes / 60
    if hours >= 100:
        return f"{hours:.0f}h"
    return f"{hours:.1f}h"


def _build_stats_comparison_visual(
    *,
    header: str,
    subheader: str,
    selected_alias: str,
    match_alias: str,
    selected_metric: int,
    match_metric: int,
    selected_display: str,
    match_display: str,
) -> str:
    ceiling = max(selected_metric, match_metric, 1)
    selected_width = (selected_metric / ceiling) * 100 if selected_metric > 0 else 0.0
    match_width = (match_metric / ceiling) * 100 if match_metric > 0 else 0.0

    def _row_markup(metric_value: int, width: float, display_value: str, role: str) -> str:
        fill_class = f"stats-bar-fill {role}"
        if metric_value > 0:
            fill_class += " has-value"
        return f"""
        <div class="stats-row">
            <div class="stats-bar-track">
                <div class="{fill_class}" style="width: {width:.1f}%">{escape(display_value)}</div>
            </div>
        </div>
        """

    selected_row = _row_markup(
        metric_value=selected_metric,
        width=selected_width,
        display_value=selected_display,
        role="selected",
    )
    match_row = _row_markup(
        metric_value=match_metric,
        width=match_width,
        display_value=match_display,
        role="match",
    )

    return f"""
    <div class="stats-panel">
        <div class="stats-header">{escape(header)}</div>
        <div class="stats-subheader">{escape(subheader)}</div>
        <div class="stats-rows">
            {selected_row}
            {match_row}
        </div>
    </div>
    """


def _build_track_visual(
    *,
    track_name: str | None,
    artist_name: str | None,
    fallback_title: str,
    fallback_subtitle: str,
    selected_alias: str,
    match_alias: str,
    selected_count: int,
    match_count: int,
) -> str:
    title = track_name or fallback_title
    subtitle = artist_name or fallback_subtitle

    return _build_stats_comparison_visual(
        header=f'"{title}"',
        subheader=subtitle,
        selected_alias=selected_alias,
        match_alias=match_alias,
        selected_metric=selected_count,
        match_metric=match_count,
        selected_display=f"{selected_count}" if selected_count > 0 else "—",
        match_display=f"{match_count}" if match_count > 0 else "—",
    )


def _build_foundation_visual(
    *,
    genre_name: str,
    selected_alias: str,
    match_alias: str,
    selected_share: float,
    match_share: float,
) -> str:
    selected_metric = max(0, int(round(selected_share * 100)))
    match_metric = max(0, int(round(match_share * 100)))
    return _build_stats_comparison_visual(
        header=f"{genre_name}",
        subheader="% of total",
        selected_alias=selected_alias,
        match_alias=match_alias,
        selected_metric=selected_metric,
        match_metric=match_metric,
        selected_display=_percent(selected_share),
        match_display=_percent(match_share),
    )


def _build_immersion_visual(
    *,
    selected_alias: str,
    match_alias: str,
    selected_minutes: int,
    match_minutes: int,
) -> str:
    return _build_stats_comparison_visual(
        header="Listening time",
        subheader="Total minutes logged",
        selected_alias=selected_alias,
        match_alias=match_alias,
        selected_metric=max(0, selected_minutes),
        match_metric=max(0, match_minutes),
        selected_display=f"{selected_minutes:,}" if selected_minutes > 0 else "—",
        match_display=f"{match_minutes:,}" if match_minutes > 0 else "—",
    )


def _build_reveal_visual(
    *,
    match_alias: str,
    predicted_similarity: float,
    top_label: str,
    top_story: str,
) -> str:
    return f"""
    <div class="match-reveal">
        <div class="reveal-hero">
            <div class="spotlight-kicker">Meet your match</div>
            <div class="spotlight-title">{escape(match_alias)}</div>
            <div class="reveal-score">{_percent(predicted_similarity)}</div>
            <div class="spotlight-subtitle">Top overlap: {escape(top_label)}</div>
        </div>
        <div class="metric-row">
            <div>
                <div class="metric-label">Why it lands</div>
                <strong>{escape(top_label)}</strong>
            </div>
            <div class="legend-meta">{escape(_short_text(top_story, 44))}</div>
        </div>
    </div>
    """


def _build_tag_visual(tags: list[str], tag_kind: str) -> str:
    cards = "".join(
        f'<div class="tag-card {tag_kind}">{escape(_short_text(tag, 72))}</div>'
        for tag in tags
    )
    return f'<div class="tag-cloud">{cards}</div>'


def _build_radar_visual(
    axes: pd.DataFrame,
    *,
    selected_alias: str,
    match_alias: str,
) -> str:
    axis_rows = axes.head(6).reset_index(drop=True)
    if axis_rows.empty:
        return '<div class="spotlight-subtitle">Radar data unavailable.</div>'

    center_x = 140.0
    center_y = 140.0
    radius = 94.0
    ring_paths: list[str] = []
    axis_lines: list[str] = []
    label_nodes: list[str] = []
    selected_points: list[str] = []
    match_points: list[str] = []

    total_axes = len(axis_rows)
    for ring in (0.25, 0.5, 0.75, 1.0):
        polygon_points = []
        for index in range(total_axes):
            angle = (-math.pi / 2) + ((2 * math.pi * index) / total_axes)
            x = center_x + math.cos(angle) * radius * ring
            y = center_y + math.sin(angle) * radius * ring
            polygon_points.append(f"{x:.1f},{y:.1f}")
        ring_paths.append(
            f'<polygon points="{" ".join(polygon_points)}" fill="none" stroke="rgba(255,255,255,0.10)" stroke-width="1" />'
        )

    for index, row in axis_rows.iterrows():
        angle = (-math.pi / 2) + ((2 * math.pi * index) / total_axes)
        outer_x = center_x + math.cos(angle) * radius
        outer_y = center_y + math.sin(angle) * radius
        label_x = center_x + math.cos(angle) * (radius + 28)
        label_y = center_y + math.sin(angle) * (radius + 20)

        axis_lines.append(
            f'<line x1="{center_x:.1f}" y1="{center_y:.1f}" x2="{outer_x:.1f}" y2="{outer_y:.1f}" stroke="rgba(255,255,255,0.10)" stroke-width="1" />'
        )
        label_nodes.append(
            f'<text x="{label_x:.1f}" y="{label_y:.1f}" fill="rgba(248,250,252,0.78)" font-size="11" text-anchor="middle" dominant-baseline="middle">{escape(_short_axis_label(str(row["label"])))}</text>'
        )

        selected_score = float(row["selected_score"])
        match_score = float(row["match_score"])
        selected_x = center_x + math.cos(angle) * radius * selected_score
        selected_y = center_y + math.sin(angle) * radius * selected_score
        match_x = center_x + math.cos(angle) * radius * match_score
        match_y = center_y + math.sin(angle) * radius * match_score
        selected_points.append(f"{selected_x:.1f},{selected_y:.1f}")
        match_points.append(f"{match_x:.1f},{match_y:.1f}")

    svg = f"""
    <svg viewBox="0 0 280 280" role="img" aria-label="Pair radar chart">
        {" ".join(ring_paths)}
        {" ".join(axis_lines)}
        <polygon points="{" ".join(selected_points)}" fill="rgba(94,194,255,0.18)" stroke="rgba(94,194,255,1)" stroke-width="2.5" />
        <polygon points="{" ".join(match_points)}" fill="rgba(246,80,143,0.18)" stroke="rgba(246,80,143,1)" stroke-width="2.5" />
        {" ".join(label_nodes)}
    </svg>
    """

    return f"""
    <div class="viz-stage">
        {svg}
        <div class="viz-legend legend-list">
            <div class="legend-row">
                <div style="display:flex; align-items:center; gap:10px;">
                    <span class="legend-dot" style="background: var(--accent-blue);"></span>
                    <div class="legend-copy">
                        <strong>{escape(selected_alias)}</strong>
                        <span class="legend-meta">Your taste shape</span>
                    </div>
                </div>
                <span class="legend-value">{_percent(axis_rows["selected_score"].mean())}</span>
            </div>
            <div class="legend-row">
                <div style="display:flex; align-items:center; gap:10px;">
                    <span class="legend-dot" style="background: var(--accent-red);"></span>
                    <div class="legend-copy">
                        <strong>{escape(match_alias)}</strong>
                        <span class="legend-meta">Match taste shape</span>
                    </div>
                </div>
                <span class="legend-value">{_percent(axis_rows["match_score"].mean())}</span>
            </div>
        </div>
    </div>
    """


def _build_dna_visual(dna_pieces: pd.DataFrame) -> str:
    rows = dna_pieces.head(4).reset_index(drop=True)
    if rows.empty:
        return '<div class="spotlight-subtitle">DNA data unavailable.</div>'

    palette = [
        "var(--accent-red)",
        "var(--accent-blue)",
        "var(--accent-green)",
        "rgba(255,255,255,0.55)",
    ]

    stops: list[str] = []
    legends: list[str] = []
    running_total = 0.0
    for index, row in rows.iterrows():
        share = float(row["dna_percentage"])
        start = running_total * 100
        running_total += share
        end = running_total * 100
        color = palette[index % len(palette)]
        stops.append(f"{color} {start:.1f}% {end:.1f}%")
        legends.append(
            f"""
            <div class="legend-row">
                <div style="display:flex; align-items:center; gap:10px;">
                    <span class="legend-dot" style="background: {color};"></span>
                    <div class="legend-copy">
                        <strong>{escape(str(row["label"]))}</strong>
                        <span class="legend-meta">{escape(_short_text(str(row["story_lead"]), 44))}</span>
                    </div>
                </div>
                <span class="legend-value">{_percent(share)}</span>
            </div>
            """
        )

    gradient = ", ".join(stops)
    return f"""
    <div class="viz-stage">
        <div class="donut-wrap" style="background: conic-gradient({gradient});">
            <div class="donut-hole">
                <div>
                    <span class="legend-meta">Match</span>
                    <strong>DNA</strong>
                </div>
            </div>
        </div>
        <div class="viz-legend legend-list">
            {"".join(legends)}
        </div>
    </div>
    """


def _build_opposites_visual(
    differences: pd.DataFrame,
    *,
    selected_alias: str,
    match_alias: str,
) -> str:
    rows = differences.head(3).reset_index(drop=True)
    if rows.empty:
        return '<div class="spotlight-subtitle">Difference data unavailable.</div>'

    html_rows = []
    for _, row in rows.iterrows():
        selected_score = float(row["selected_score"])
        match_score = float(row["match_score"])
        start = min(selected_score, match_score) * 100
        span = abs(selected_score - match_score) * 100
        html_rows.append(
            f"""
            <div class="opposite-row">
                <div class="opposite-label">{escape(str(row["label"]))}</div>
                <div class="opposite-track">
                    <div class="opposite-span" style="left: {start:.1f}%; width: {span:.1f}%"></div>
                    <div class="opposite-point selected" style="left: {selected_score * 100:.1f}%"></div>
                    <div class="opposite-point match" style="left: {match_score * 100:.1f}%"></div>
                </div>
                <div class="opposite-meta">
                    <span>{escape(selected_alias)} {_percent(selected_score)}</span>
                    <span>{escape(match_alias)} {_percent(match_score)}</span>
                </div>
            </div>
            """
        )

    return f'<div class="opposites-stack">{"".join(html_rows)}</div>'


def _build_stats_screens(
    context: PairContext,
    config: DashboardConfig,
) -> list[Screen]:
    del config
    snapshot = _compute_pair_history_snapshot(
        selected_user_id=context.selected_user_id,
        match_user_id=context.match_user_id,
        artifact_root=str(CONFIG.paths.artifact_root),
    )
    top_signal = context.group_rankings.iloc[0]

    track_visual = _build_track_visual(
        track_name=snapshot.shared_track_name if snapshot else None,
        artist_name=snapshot.shared_track_artist if snapshot else None,
        fallback_title=snapshot.shared_artist_name
        if snapshot and snapshot.shared_artist_name
        else _title_case(str(top_signal["label"]), "Shared Taste"),
        fallback_subtitle="Exact song overlap not found, so the screen falls back to the strongest shared orbit.",
        selected_alias=context.selected_alias,
        match_alias=context.match_alias,
        selected_count=snapshot.shared_track_selected_count if snapshot else 0,
        match_count=snapshot.shared_track_match_count if snapshot else 0,
    )

    genre_name = (
        _title_case(
            snapshot.shared_genre_name,
            _title_case(str(top_signal["label"]), "Shared Taste"),
        )
        if snapshot
        else _title_case(str(top_signal["label"]), "Shared Taste")
    )
    selected_share = (
        snapshot.shared_genre_selected_share
        if snapshot and snapshot.shared_genre_name
        else float(top_signal["selected_score"])
    )
    match_share = (
        snapshot.shared_genre_match_share
        if snapshot and snapshot.shared_genre_name
        else float(top_signal["match_score"])
    )
    foundation_visual = _build_foundation_visual(
        genre_name=genre_name,
        selected_alias=context.selected_alias,
        match_alias=context.match_alias,
        selected_share=selected_share,
        match_share=match_share,
    )

    immersion_visual = _build_immersion_visual(
        selected_alias=context.selected_alias,
        match_alias=context.match_alias,
        selected_minutes=snapshot.selected_minutes if snapshot else 0,
        match_minutes=snapshot.match_minutes if snapshot else 0,
    )

    return [
        Screen(
            eyebrow="",
            title="",
            subtitle="",
            visual_html=track_visual,
        ),
        Screen(
            eyebrow="",
            title="",
            subtitle="",
            visual_html=foundation_visual,
        ),
        Screen(
            eyebrow="",
            title="",
            subtitle="",
            visual_html=immersion_visual,
        ),
    ]


def _build_match_reveal_screens(
    context: PairContext,
    config: DashboardConfig,
) -> list[Screen]:
    quirks_payload = QuirksIdea().build(context, config)
    top_signal = context.group_rankings.iloc[0]

    green_flags = quirks_payload.green_flags[:3]
    match_quirks = quirks_payload.match_quirks[:3]

    return [
        Screen(
            eyebrow="Match Reveal",
            title="First, reveal the person",
            subtitle="A recommendation should feel social before it feels analytical.",
            visual_html=_build_reveal_visual(
                match_alias=context.match_alias,
                predicted_similarity=context.predicted_similarity,
                top_label=str(top_signal["label"]),
                top_story=str(top_signal["story_lead"]),
            ),
            body="The first tap answers the emotional question: who is this match?",
            footer="Then the next taps can explain why the model felt confident without breaking the mood.",
        ),
        Screen(
            eyebrow="Match Reveal",
            title="Shared Green Flags",
            subtitle="Surface what already feels affirming between the pair.",
            visual_html=_build_tag_visual(green_flags, "good"),
            body="Positive language keeps the explanation warm and easy to scan.",
            footer="These are the pair traits we would want users to screenshot or send to a friend.",
        ),
        Screen(
            eyebrow="Match Reveal",
            title="Match Quirks",
            subtitle="Then reveal the harmless weirdness that makes the person memorable.",
            visual_html=_build_tag_visual(match_quirks, "quirk"),
            body="Quirks make the recommendation feel human instead of machine-generated.",
            footer=f"This last screen stays focused on {context.match_alias}, so the reveal still feels like discovery.",
        ),
    ]


def _build_visualization_screens(
    context: PairContext,
    config: DashboardConfig,
) -> list[Screen]:
    radar_payload = NewRadarIdea().build(context, config)
    dna_payload = MatchDNAIdea().build(context, config)
    opposites_payload = OppositesIdea().build(context, config)

    return [
        Screen(
            eyebrow="Visualizations",
            title="Radar",
            subtitle="A fast read on where the pair moves together.",
            visual_html=_build_radar_visual(
                radar_payload.axes,
                selected_alias=context.selected_alias,
                match_alias=context.match_alias,
            ),
        ),
        Screen(
            eyebrow="Visualizations",
            title="DNA Breakdown",
            subtitle="A composition view of what drives the match.",
            visual_html=_build_dna_visual(dna_payload.dna_pieces),
        ),
        Screen(
            eyebrow="Visualizations",
            title="Opposites Attract",
            subtitle="Useful contrast, kept legible.",
            visual_html=_build_opposites_visual(
                opposites_payload.differences,
                selected_alias=context.selected_alias,
                match_alias=context.match_alias,
            ),
        ),
    ]


def _render_concept_header(number: int, title: str, summary: str) -> None:
    st.markdown(
        f"""
        <div class="concept-header">
            <p class="concept-kicker">Idea {number:02d}</p>
            <h2 class="concept-title">{escape(title)}</h2>
            <p class="concept-summary">{escape(summary)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_model_lens(context: PairContext, config: DashboardConfig) -> None:
    family_summary = next(
        family.summary
        for family in config.model_families
        if family.key == context.model_key
    )
    most_different = (
        context.group_rankings.assign(
            difference=(
                context.group_rankings["selected_score"]
                - context.group_rankings["match_score"]
            ).abs()
        )
        .sort_values("difference", ascending=False)
        .iloc[0]
    )
    top_signal = context.group_rankings.iloc[0]

    st.markdown(
        """
        <div class="model-lens-shell">
            <p class="concept-kicker">What The Model Sees</p>
            <h2 class="concept-title">It compares listening patterns, not vibes.</h2>
            <p class="concept-summary">
                Every user becomes a compact taste profile built from past listening behavior.
                The model compares those profiles, looks for overlap plus legible contrast,
                and estimates whether that pattern tends to hold up over time.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    card_html = [
        (
            "Input",
            "Past listening history",
            "Energy, tempo, mood, loyalty, exploration, and genre breadth become numeric signals the model can compare.",
        ),
        (
            "Pair logic",
            f"Shared signal: {top_signal['label']}",
            f"The strongest overlap in this pair is {top_signal['label'].lower()}, while {most_different['label'].lower()} adds the clearest contrast.",
        ),
        (
            "Output",
            f"{context.model_label} score",
            _short_text(family_summary, 140),
        ),
    ]

    columns = st.columns(3)
    for column, (kicker, title, body) in zip(columns, card_html, strict=False):
        with column:
            st.markdown(
                f"""
                <div class="lens-card">
                    <p class="lens-kicker">{escape(kicker)}</p>
                    <h3>{escape(title)}</h3>
                    <p>{escape(body)}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        f"""
        <div class="lens-chip-row">
            <span class="lens-chip">Model: {escape(context.model_label)}</span>
            <span class="lens-chip">Predicted similarity: {_percent(context.predicted_similarity)}</span>
            <span class="lens-chip">Future alignment: {_percent(context.future_alignment_score)}</span>
            <span class="lens-chip">Top shared trait: {escape(str(top_signal["label"]))}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_implementation_ideas_grid(
    context: PairContext,
    config: DashboardConfig = CONFIG,
) -> None:
    _inject_showcase_styles()

    concepts = _build_concept_specs(context, config)

    columns = st.columns(3, gap="medium")
    for column, concept in zip(columns, concepts, strict=False):
        with column:
            render_phone_concept_card(
                concept_key=concept.concept_key,
                card_label=concept.card_label,
                card_description=concept.card_description,
                selected_alias=context.selected_alias,
                match_alias=context.match_alias,
                match_score=context.predicted_similarity,
                screens=concept.screens,
                height=concept.height,
                phone_height=concept.phone_height,
                phone_width=concept.phone_width,
            )


def _build_concept_specs(
    context: PairContext,
    config: DashboardConfig,
) -> list[ConceptCardSpec]:
    return [
        _build_statistics_concept_spec(context, config),
        ConceptCardSpec(
            concept_key=f"match-reveal-{context.selected_user_id}-{context.match_user_id}",
            card_label="Match Reveal",
            card_description=(
                "Presents shared traits and memorable quirks instead of abstract "
                "confidence language."
            ),
            screens=_build_match_reveal_screens(context, config),
            height=920,
            phone_height=675,
            phone_width=304,
        ),
        ConceptCardSpec(
            concept_key=f"visualizations-{context.selected_user_id}-{context.match_user_id}",
            card_label="Visualizations",
            card_description=(
                "Lets the user inspect overall shape, feature mix, and productive "
                "difference."
            ),
            screens=_build_visualization_screens(context, config),
            height=920,
            phone_height=675,
            phone_width=304,
        ),
    ]


def _build_statistics_concept_spec(
    context: PairContext,
    config: DashboardConfig,
) -> ConceptCardSpec:
    return ConceptCardSpec(
        concept_key=f"statistics-{context.selected_user_id}-{context.match_user_id}",
        card_label="Shared Proof",
        card_description=(
            "A one tap story arc: starting with shared tracks, widened to context "
            "via genres, then close on listening depth."
        ),
        screens=_build_stats_screens(context, config),
        height=900,
        phone_height=666,
        phone_width=300,
    )


def render_model_explanation_section(
    context: PairContext,
    config: DashboardConfig = CONFIG,
) -> None:
    _inject_showcase_styles()

    family_summary = next(
        family.summary
        for family in config.model_families
        if family.key == context.model_key
    )
    most_different = (
        context.group_rankings.assign(
            difference=(
                context.group_rankings["selected_score"]
                - context.group_rankings["match_score"]
            ).abs()
        )
        .sort_values("difference", ascending=False)
        .iloc[0]
    )
    top_signal = context.group_rankings.iloc[0]
    quirks_payload = QuirksIdea().build(context, config)

    green_flag = (
        quirks_payload.green_flags[0]
        if quirks_payload.green_flags
        else "Shared habits the pair can immediately recognize."
    )
    quirk = (
        quirks_payload.match_quirks[0]
        if quirks_payload.match_quirks
        else "A small taste difference that keeps the match interesting."
    )

    st.markdown(
        f"""
        <div class="model-process-shell">
            <div class="model-process-grid">
                <div class="model-stage">
                    <p class="model-stage-kicker">Model Input</p>
                    <div class="model-stage-icons">
                        <span class="model-icon-chip">🎵</span>
                        <span class="model-icon-chip">🎶</span>
                        <span class="model-icon-chip">👤</span>
                    </div>
                    <h3 class="model-stage-title">Listening history becomes usable signal</h3>
                    <p class="model-stage-body">
                        Past songs, genres, replay behavior, and exploration patterns become
                        numeric features the model can compare.
                    </p>
                    <div class="model-avatar-row">
                        <span class="model-avatar-chip selected">{escape(context.selected_alias[:2].upper())}</span>
                        <span class="model-avatar-chip match">{escape(context.match_alias[:2].upper())}</span>
                        <span class="model-avatar-chip neutral">{escape(context.model_label[:2].upper())}</span>
                    </div>
                </div>
                <div class="model-arrow">→</div>
                <div class="model-stage">
                    <p class="model-stage-kicker">Model Processing ({escape(context.model_label)})</p>
                    <div class="model-stage-icons">
                        <span class="model-icon-chip">⚙️</span>
                        <span class="model-icon-chip">🧠</span>
                        <span class="model-icon-chip">AI</span>
                    </div>
                    <h3 class="model-stage-title">Overlap plus contrast become a match story</h3>
                    <p class="model-stage-body">
                        The model weighs strong shared signals like {escape(str(top_signal["label"]).lower())}
                        while noticing contrasts like {escape(str(most_different["label"]).lower())}
                        that can still feel complementary.
                    </p>
                </div>
                <div class="model-arrow">→</div>
                <div class="model-output-list">
                    <div class="model-output-row">
                        <span class="model-output-icon">🎼</span>
                        <div>
                            <h3 class="model-output-title">Key Shared Statistics</h3>
                            <p class="model-output-body">Common songs, genre floor, and listening depth.</p>
                        </div>
                    </div>
                    <div class="model-output-row">
                        <span class="model-output-icon">👍</span>
                        <div>
                            <h3 class="model-output-title">Specific Connection Points</h3>
                            <p class="model-output-body">{escape(_short_text(f"{green_flag} {quirk}", 118))}</p>
                        </div>
                    </div>
                    <div class="model-output-row">
                        <span class="model-output-icon">📊</span>
                        <div>
                            <h3 class="model-output-title">Holistic Taste Alignment</h3>
                            <p class="model-output-body">
                                Radar, DNA, and contrast visuals make the score legible for non-specialists.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
            <div class="model-summary-shell">
                <p>
                    <strong>Model Input:</strong> music and user history.
                    <strong> Processing:</strong> {escape(_short_text(family_summary, 112))}
                    <strong> Output:</strong> a usable product story built from shared proof, memorable details,
                    and clear visuals.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_implementation_ideas(
    context: PairContext,
    config: DashboardConfig = CONFIG,
) -> None:
    # Legacy renderer preserved for reference during the redesign.
    # ideas = get_implementation_ideas()
    # review_order = " · ".join(
    #     f"{index}. {idea.title}" for index, idea in enumerate(ideas, start=1)
    # )
    #
    # st.markdown(f"## {config.ui.implementation_section_title}")
    # st.markdown(
    #     "Each concept below is stacked in presentation order so the team can review the "
    #     "full set of directions in one pass. Every module still runs off the selected "
    #     "user and model family, so the story changes when you swap either input."
    # )
    # st.caption(f"Review order: {review_order}")
    #
    # for index, idea in enumerate(ideas, start=1):
    #     st.markdown(f"### Concept {index:02d}")
    #     payload = idea.build(context, config)
    #     idea.render(payload, context, config)
    #     if index < len(ideas):
    #         st.divider()

    # Legacy vertical layout preserved for reference while the page shell now
    # composes the dashboard in app.py.
    #
    # _inject_showcase_styles()
    #
    # concepts = [
    #     (
    #         1,
    #         "Statistics",
    #         "The most direct production path: simple, tangible proof that the match is grounded in real listening overlap.",
    #         _build_stats_screens(context, config),
    #         860,
    #     ),
    #     (
    #         2,
    #         "Match Reveal",
    #         "The most playful path: make the recommendation feel like a person first, then reveal the reasons in sequence.",
    #         _build_match_reveal_screens(context, config),
    #         860,
    #     ),
    #     (
    #         3,
    #         "Visualizations",
    #         "The richest explanatory path: compact charts for users who want to inspect how different patterns shape the outcome.",
    #         _build_visualization_screens(context, config),
    #         900,
    #     ),
    # ]
    #
    # for number, title, summary, screens, height in concepts:
    #     _render_concept_header(number, title, summary)
    #     render_phone_screens(
    #         concept_key=f"{title}-{context.selected_user_id}-{context.match_user_id}",
    #         selected_alias=context.selected_alias,
    #         match_alias=context.match_alias,
    #         match_score=context.predicted_similarity,
    #         screens=screens,
    #         height=height,
    #     )
    #     if number < len(concepts):
    #         st.markdown('<div class="concept-gap"></div>', unsafe_allow_html=True)
    #
    # _render_model_lens(context, config)

    render_implementation_ideas_grid(context, config)
    render_model_explanation_section(context, config)
