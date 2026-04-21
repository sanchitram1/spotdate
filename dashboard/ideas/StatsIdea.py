from __future__ import annotations

import csv
import os
from dataclasses import dataclass

import streamlit as st

from dashboard.config import CONFIG, DashboardConfig
from dashboard.ideas.base import ImplementationIdea
from dashboard.types import PairContext


@dataclass(frozen=True)
class StatsPayload:
    # Card 1: Artist
    artist_title: str
    artist_body: str

    # Card 2: Genre
    genre_title: str
    genre_body: str

    # Card 3: Time
    time_title: str
    time_body: str

    # Card 4: Style
    style_title: str
    style_body: str


@st.cache_data(ttl=3600)
def compute_real_stats(user_id1: str, user_id2: str) -> dict:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    csv_path = os.path.join(project_root, "data", "users_with_tracks.csv")
    
    if not os.path.exists(csv_path):
        return {}

    p1_artists = {}
    p2_artists = {}
    p1_genres = {}
    p2_genres = {}
    duration1 = 0
    duration2 = 0

    # Using streaming CSV reader instead of pd.read_csv to process the large file efficiently in O(1) memory
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            uid = row.get("user_id")
            if uid == user_id1:
                artist = row.get("artist")
                if artist:
                    p1_artists[artist] = p1_artists.get(artist, 0) + 1
                genre = row.get("genre")
                if genre:
                    p1_genres[genre] = p1_genres.get(genre, 0) + 1
                dur = row.get("duration_ms")
                if dur and dur.isdigit():
                    duration1 += int(dur)

            elif uid == user_id2:
                artist = row.get("artist")
                if artist:
                    p2_artists[artist] = p2_artists.get(artist, 0) + 1
                genre = row.get("genre")
                if genre:
                    p2_genres[genre] = p2_genres.get(genre, 0) + 1
                dur = row.get("duration_ms")
                if dur and dur.isdigit():
                    duration2 += int(dur)

    def get_top(d, n=5):
        return [
            k for k, v in sorted(d.items(), key=lambda item: item[1], reverse=True)[:n]
        ]

    return {
        "p1_artists": get_top(p1_artists, 5),
        "p2_artists": get_top(p2_artists, 5),
        "p1_genres": get_top(p1_genres, 3),
        "p2_genres": get_top(p2_genres, 3),
        "time1": duration1 // 60000,
        "time2": duration2 // 60000,
    }


class StatsIdea(ImplementationIdea):
    key = "stats"
    title = "Real Listening Highlights"
    kind = "Statistics"
    description = (
        "Four highlights uncovering your specific shared artists, genres, "
        "and total listening times based on actual track records."
    )

    def build(
        self, context: PairContext, config: DashboardConfig = CONFIG
    ) -> StatsPayload:
        p1 = context.selected_profile
        p2 = context.match_profile
        alias2 = context.match_alias

        # Calculate REAL stats from the raw dataset
        stats = compute_real_stats(context.selected_user_id, context.match_user_id)

        if stats:
            p1_artists = stats["p1_artists"]
            p2_artists = stats["p2_artists"]
            p1_genres = stats["p1_genres"]
            p2_genres = stats["p2_genres"]
            time1 = stats["time1"]
            time2 = stats["time2"]
        else:
            p1_artists, p2_artists = [], []
            p1_genres, p2_genres = [], []
            time1, time2 = 0, 0

        # --- Card 1: Artist Clash / Match ---
        shared_artists = [a for a in p1_artists if a in p2_artists]

        if len(shared_artists) > 0:
            artist_title = "Shared Obsessions"
            artist_body = f"Both of you have **{shared_artists[0]}** on heavy rotation!"
            if len(shared_artists) > 1:
                artist_body += f" You also both love **{shared_artists[1]}**."
        elif p1_artists and p2_artists:
            artist_title = "Taste Collision"
            artist_body = f"Your top artist is **{p1_artists[0]}**, while {alias2} is obsessed with **{p2_artists[0]}**."
        else:
            artist_title = "Exploring Artists"
            artist_body = "You are both exploring a diverse and unique set of artists!"

        # --- Card 2: Genre Venn Diagram ---
        shared_genres = [g for g in p1_genres if g in p2_genres]

        if shared_genres:
            genre_title = "Common Ground"
            genre_body = f"Your musical foundation is **{shared_genres[0].title()}**! "
            diff_p1 = [g for g in p1_genres if g not in shared_genres]
            diff_p2 = [g for g in p2_genres if g not in shared_genres]
            if diff_p1 and diff_p2:
                genre_body += f"But you lean more into **{diff_p1[0].title()}**, while {alias2} leans into **{diff_p2[0].title()}**."
        elif p1_genres and p2_genres:
            genre_title = "Different Worlds"
            genre_body = f"You live in the world of **{p1_genres[0].title()}**, while {alias2} surrounds themselves with **{p2_genres[0].title()}**."
        else:
            genre_title = "Music Lovers"
            genre_body = "You both enjoy a vast and eclectic mix of musical genres."

        # --- Card 3: Total Listening Time ---
        if time1 > 0 and time2 > 0:
            time_title = "Music Immersion"
            time_body = f"You spent **{time1:,} minutes** listening to music, while {alias2} clocked in **{time2:,} minutes**!"
            if time1 > time2 * 1.5:
                time_body += " You are definitely the more hardcore listener here."
            elif time2 > time1 * 1.5:
                time_body += f" {alias2} is definitely the more hardcore listener here."
            else:
                time_body += " You both have very similar dedication to your tunes."
        else:
            # Fallback if no raw track data
            peak1 = p1.get("temporal_peak_hour", 12)
            time_title = "Music Time"
            time_body = f"Your music peaks around {int(peak1)}:00."

        # --- Card 4: Listening Style ---
        ent1 = p1.get("artist_entropy", 0.5)
        ent2 = p2.get("artist_entropy", 0.5)

        def style_label(entropy):
            return "Explorer" if entropy > 5.0 else "Loyalist"

        style1 = style_label(ent1)
        style2 = style_label(ent2)

        if style1 == style2 == "Explorer":
            style_title = "Avid Explorers"
            style_body = "You both have an insatiable appetite for discovering new artists and tracks!"
        elif style1 == style2 == "Loyalist":
            style_title = "Track Loopers"
            style_body = "You are both fiercely loyal listeners. When you love an artist, you keep them on repeat."
        else:
            style_title = "Opposites Attract"
            style_body = f"You are an **{style1}**, while {alias2} is a **{style2}** when it comes to discovering music."

        return StatsPayload(
            artist_title=artist_title,
            artist_body=artist_body,
            genre_title=genre_title,
            genre_body=genre_body,
            time_title=time_title,
            time_body=time_body,
            style_title=style_title,
            style_body=style_body,
        )

    def render(
        self,
        payload: StatsPayload,
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

        st.markdown(
            """
            <style>
            .stats-container {
                display: flex;
                flex-direction: row;
                gap: 20px;
                justify-content: space-between;
                margin-top: 20px;
                margin-bottom: 20px;
            }
            .stat-card {
                flex: 1;
                border: 2px solid rgba(255, 255, 255, 0.2);
                border-radius: 16px;
                padding: 30px 20px;
                min-height: 220px;
                display: flex;
                flex-direction: column;
                justify-content: flex-start;
                align-items: flex-start;
                background-color: rgba(255, 255, 255, 0.05);
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                transition: transform 0.2s ease-in-out;
            }
            .stat-card:hover {
                transform: translateY(-5px);
                border-color: rgba(255, 255, 255, 0.4);
            }
            .stat-card h4 {
                margin-top: 0;
                margin-bottom: 15px;
                color: #e0e0e0;
                font-size: 1.2em;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                padding-bottom: 10px;
                width: 100%;
            }
            .stat-card p {
                margin: 0;
                line-height: 1.6;
                color: #ffffff;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="stats-container">
                <div class="stat-card">
                    <h4>{payload.artist_title}</h4>
                    <p>{payload.artist_body}</p>
                </div>
                <div class="stat-card">
                    <h4>{payload.genre_title}</h4>
                    <p>{payload.genre_body}</p>
                </div>
                <div class="stat-card">
                    <h4>{payload.time_title}</h4>
                    <p>{payload.time_body}</p>
                </div>
                <div class="stat-card">
                    <h4>{payload.style_title}</h4>
                    <p>{payload.style_body}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
