from __future__ import annotations

import uuid
from dataclasses import dataclass

import streamlit as st

from dashboard.config import CONFIG, DashboardConfig
from dashboard.ideas.base import ImplementationIdea
from dashboard.types import PairContext


@dataclass(frozen=True)
class FlipCardPayload:
    match_alias: str
    top_shared_label: str
    top_shared_score: float
    future_alignment: float | None
    predicted_similarity: float


class FlipCardIdea(ImplementationIdea):
    key = "flip_card"
    title = "Match Reveal (Click to Flip)"
    kind = "Interactive Component"
    description = (
        "A playful CSS-based flip card that hides the match's stats on the back. "
        "Users click the card on the front to reveal the match's core stats and alignment scores."
    )

    def build(
        self, context: PairContext, config: DashboardConfig = CONFIG
    ) -> FlipCardPayload:
        top_group = context.group_rankings.iloc[0]

        return FlipCardPayload(
            match_alias=context.match_alias,
            top_shared_label=top_group["label"],
            top_shared_score=float(top_group["pair_score"]),
            future_alignment=context.future_alignment_score,
            predicted_similarity=context.predicted_similarity,
        )

    def render(
        self,
        payload: FlipCardPayload,
        context: PairContext,
        config: DashboardConfig = CONFIG,
    ) -> None:
        st.markdown(
            f"""
            <div class="idea-header">
                <p class="idea-kicker">{self.kind}</p>
                <h3>{self.title}</h3>
                <p>{self.description}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        future_align_text = (
            f"{payload.future_alignment:.0%}"
            if payload.future_alignment is not None
            else "N/A"
        )

        # Unique ID for the checkbox to ensure multiple cards wouldn't conflict
        checkbox_id = f"flip-{uuid.uuid4().hex[:8]}"

        html = f"""
        <style>
        .flip-card-container {{
            display: flex;
            justify-content: center;
            margin: 30px 0;
            width: 100%;
        }}
        .flip-box {{
            background-color: transparent;
            width: 320px;
            height: 420px;
            perspective: 1000px; /* 3D effect */
            cursor: pointer;
        }}
        .flip-box-inner {{
            position: relative;
            width: 100%;
            height: 100%;
            text-align: center;
            transition: transform 0.6s cubic-bezier(0.4, 0.2, 0.2, 1);
            transform-style: preserve-3d;
        }}
        /* Hidden checkbox hack */
        #{checkbox_id} {{
            display: none;
        }}
        #{checkbox_id}:checked ~ .flip-box .flip-box-inner {{
            transform: rotateY(180deg);
        }}
        
        .flip-box-front, .flip-box-back {{
            position: absolute;
            width: 100%;
            height: 100%;
            -webkit-backface-visibility: hidden; /* Safari */
            backface-visibility: hidden;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 30px;
            box-sizing: border-box;
        }}
        
        .flip-box-front {{
            background: linear-gradient(145deg, {config.style.panel_background}, #111e32);
            border: 1px solid rgba(255,255,255,0.05);
            color: {config.style.text_primary};
        }}
        
        .flip-box-front h1 {{
            font-size: 2.5em;
            margin: 10px 0 5px 0;
            background: -webkit-linear-gradient({config.style.accent}, {config.style.accent_tertiary});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            line-height: 1.2;
        }}
        
        .flip-box-back {{
            background: linear-gradient(135deg, {config.style.accent}, {config.style.accent_secondary});
            color: white;
            transform: rotateY(180deg);
        }}
        
        .flip-box-back h2 {{
            margin-top: 0;
            border-bottom: 2px solid rgba(255,255,255,0.3);
            padding-bottom: 15px;
            width: 100%;
        }}
        
        .stat-row {{
            display: flex;
            justify-content: space-between;
            width: 100%;
            margin: 18px 0;
            font-size: 1.1em;
            font-weight: 500;
        }}
        </style>

        <div class="flip-card-container">
            <label style="margin: 0; padding: 0; display: block; max-width: 100%;">
                <input type="checkbox" id="{checkbox_id}">
                <div class="flip-box">
                    <div class="flip-box-inner">
                        <div class="flip-box-front">
                            <p style="text-transform: uppercase; letter-spacing: 3px; color: {config.style.text_muted}; font-size:0.8em; margin:0;">New Match</p>
                            <h1>{payload.match_alias}</h1>
                            <div style="margin-top: 40px; width: 50px; height: 50px; border-radius: 50%; border: 2px solid {config.style.accent}; display: flex; justify-content: center; align-items: center;">
                                <span style="font-size: 1.5em; color: {config.style.accent};">👆</span>
                            </div>
                            <p style="margin-top: 15px; font-size: 0.9em; color: {config.style.text_muted};">Click to flip</p>
                        </div>
                        <div class="flip-box-back">
                            <h2>Match Stats</h2>
                            <div class="stat-row">
                                <span>Model Confidence</span>
                                <span>{payload.predicted_similarity:.0%}</span>
                            </div>
                            <div class="stat-row">
                                <span>Future Alignment</span>
                                <span>{future_align_text}</span>
                            </div>
                            <div style="margin-top: auto; padding: 20px; background: rgba(0,0,0,0.25); border-radius: 14px; width: 100%; box-sizing: border-box;">
                                <p style="margin: 0; font-size: 0.85em; text-transform: uppercase; letter-spacing: 1px; opacity: 0.8;">Top Shared Trait</p>
                                <p style="margin: 8px 0 0 0; font-size: 1.4em; font-weight: bold;">{payload.top_shared_label}</p>
                                <p style="margin: 4px 0 0 0; font-size: 1em; opacity: 0.9;">{payload.top_shared_score:.0%} Match</p>
                            </div>
                        </div>
                    </div>
                </div>
            </label>
        </div>
        """

        st.markdown(html, unsafe_allow_html=True)
