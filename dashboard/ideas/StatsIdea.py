from __future__ import annotations

import csv
from pathlib import Path
from dataclasses import dataclass

import streamlit as st

from dashboard.config import CONFIG, DashboardConfig
from dashboard.services.data import detect_delimiter
from dashboard.services.gcs_listening import resolve_listening_history_csv_path
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
    csv_path_o = resolve_listening_history_csv_path(CONFIG.paths)
    if csv_path_o is None or not csv_path_o.is_file():
        return {}
    csv_path = str(csv_path_o)

    p1_artists = {}
    p2_artists = {}
    p1_genres = {}
    p2_genres = {}
    duration1 = 0
    duration2 = 0

    # Using streaming CSV reader instead of pd.read_csv to process the large file efficiently in O(1) memory
    delim = detect_delimiter(Path(csv_path))
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=delim)
        for row in reader:
            uid = row.get("user_id")
            if uid == user_id1:
                artist = row.get("artist_name")
                if artist:
                    p1_artists[artist] = p1_artists.get(artist, 0) + 1
                genre = row.get("genre")
                if genre:
                    p1_genres[genre] = p1_genres.get(genre, 0) + 1
                dur = row.get("duration_ms")
                if dur and dur.isdigit():
                    duration1 += int(dur)

            elif uid == user_id2:
                artist = row.get("artist_name")
                if artist:
                    p2_artists[artist] = p2_artists.get(artist, 0) + 1
                genre = row.get("genre")
                if genre:
                    p2_genres[genre] = p2_genres.get(genre, 0) + 1
                dur = row.get("duration_ms")
                if dur and dur.isdigit():
                    duration2 += int(dur)

    return {
        "p1_artists_counts": p1_artists,
        "p2_artists_counts": p2_artists,
        "p1_genres_counts": p1_genres,
        "p2_genres_counts": p2_genres,
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
            p1_art_counts = stats["p1_artists_counts"]
            p2_art_counts = stats["p2_artists_counts"]
            p1_gen_counts = stats["p1_genres_counts"]
            p2_gen_counts = stats["p2_genres_counts"]
            time1 = stats["time1"]
            time2 = stats["time2"]
        else:
            p1_art_counts, p2_art_counts = {}, {}
            p1_gen_counts, p2_gen_counts = {}, {}
            time1, time2 = 0, 0

        def get_top_keys(d, n=5):
            return [
                k
                for k, v in sorted(d.items(), key=lambda item: item[1], reverse=True)[
                    :n
                ]
            ]

        p1_top_artists = get_top_keys(p1_art_counts, 5)
        p2_top_artists = get_top_keys(p2_art_counts, 5)
        p1_top_genres = get_top_keys(p1_gen_counts, 3)
        p2_top_genres = get_top_keys(p2_gen_counts, 3)

        # --- Card 1: Artist Clash / Match ---
        # Find ANY shared artist across their entire history, sorted by combined popularity
        shared_artist_names = set(p1_art_counts.keys()).intersection(
            set(p2_art_counts.keys())
        )
        shared_artists = sorted(
            list(shared_artist_names),
            key=lambda a: p1_art_counts[a] + p2_art_counts[a],
            reverse=True,
        )

        if len(shared_artists) > 0:
            artist_title = "🎵 Shared Obsessions"
            artist_body = f"It's a match! Both of you have **{shared_artists[0]}** on heavy rotation."
            if len(shared_artists) > 1:
                artist_body += (
                    f" You also share a mutual love for **{shared_artists[1]}**."
                )
        elif p1_top_artists and p2_top_artists:
            artist_title = "💥 Taste Collision"
            artist_body = f"Your top artist is **{p1_top_artists[0]}**, while {alias2} is obsessed with **{p2_top_artists[0]}**. A perfect chance to swap playlists!"
        else:
            artist_title = "🎧 Exploring Artists"
            artist_body = "You are both exploring a diverse and unique set of artists!"

        # --- Card 2: Genre Venn Diagram ---
        # Find ANY shared genre across their entire history
        shared_genre_names = set(p1_gen_counts.keys()).intersection(
            set(p2_gen_counts.keys())
        )
        shared_genres = sorted(
            list(shared_genre_names),
            key=lambda g: p1_gen_counts[g] + p2_gen_counts[g],
            reverse=True,
        )

        if shared_genres:
            genre_title = "💿 Common Ground"
            genre_body = f"Your musical foundation is deeply rooted in <span class='highlight-text'>{shared_genres[0].title()}</span>."

            # Find their unique divergent genres globally
            diff_p1 = [g for g in p1_gen_counts.keys() if g != shared_genres[0]]
            diff_p1 = sorted(diff_p1, key=lambda x: p1_gen_counts[x], reverse=True)

            diff_p2 = [g for g in p2_gen_counts.keys() if g != shared_genres[0]]
            diff_p2 = sorted(diff_p2, key=lambda x: p2_gen_counts[x], reverse=True)

            if diff_p1 and diff_p2:
                genre_body += f"<br><br>Outside of that, your unique vibe pulls towards **{diff_p1[0].title()}**, while {alias2} grooves more to **{diff_p2[0].title()}**."
        elif p1_top_genres and p2_top_genres:
            genre_title = "🌌 Different Worlds"
            genre_body = f"You live in the world of **{p1_top_genres[0].title()}**, while {alias2} surrounds themselves with **{p2_top_genres[0].title()}**."
        else:
            genre_title = "🎶 Music Lovers"
            genre_body = "You both enjoy a vast and eclectic mix of musical genres."

        # --- Card 3: Total Listening Time ---
        if time1 > 0 and time2 > 0:
            time_title = "⏱️ Music Immersion"
            time_body = f"You've spent <span class='highlight-text'>{time1:,} mins</span> immersed in music, while {alias2} clocked in <span class='highlight-text'>{time2:,} mins</span>."
            if time1 > time2 * 1.5:
                time_body += (
                    "<br><br>You are definitely the more hardcore listener here! 🎧"
                )
            elif time2 > time1 * 1.5:
                time_body += f"<br><br>{alias2} is definitely the more hardcore listener here! 🎧"
            else:
                time_body += "<br><br>You both share an equally intense dedication to your tunes. 🔥"
        else:
            # Fallback if no raw track data
            peak1 = p1.get("temporal_peak_hour", 12)
            time_title = "🌙 Music Time"
            time_body = f"Your music peaks around **{int(peak1)}:00**."

        # --- Card 4: Listening Style ---
        ent1 = p1.get("artist_entropy", 0.5)
        ent2 = p2.get("artist_entropy", 0.5)

        def style_label(entropy):
            return "Explorer" if entropy > 5.0 else "Loyalist"

        style1 = style_label(ent1)
        style2 = style_label(ent2)

        if style1 == style2 == "Explorer":
            style_title = "🌍 Avid Explorers"
            style_body = "Both of you have an insatiable appetite for discovering new artists and hunting down fresh tracks!"
        elif style1 == style2 == "Loyalist":
            style_title = "🔁 Track Loopers"
            style_body = "You are both fiercely loyal listeners. When you find an artist you love, they stay on loop forever."
        else:
            style_title = "🧲 Opposites Attract"
            style_body = f"You are a natural **{style1}**, while {alias2} is a true **{style2}** when it comes to consuming music."

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
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
                gap: 24px;
                margin-top: 25px;
                margin-bottom: 30px;
            }
            .stat-card {
                position: relative;
                border-radius: 20px;
                padding: 30px 25px;
                min-height: 240px;
                display: flex;
                flex-direction: column;
                justify-content: flex-start;
                align-items: flex-start;
                background: linear-gradient(145deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.02) 100%);
                border: 1px solid rgba(255, 255, 255, 0.1);
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
                backdrop-filter: blur(10px);
                -webkit-backdrop-filter: blur(10px);
                transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
                overflow: hidden;
            }
            .stat-card::before {
                content: "";
                position: absolute;
                top: 0; left: 0; right: 0;
                height: 4px;
                background: linear-gradient(90deg, #4dd7a8, #5ec2ff);
                opacity: 0;
                transition: opacity 0.3s ease;
            }
            .stat-card:hover {
                transform: translateY(-8px);
                border-color: rgba(255, 255, 255, 0.25);
                box-shadow: 0 15px 40px 0 rgba(0, 0, 0, 0.4);
            }
            .stat-card:hover::before {
                opacity: 1;
            }
            .stat-card h4 {
                margin-top: 0;
                margin-bottom: 20px;
                color: #ffffff;
                font-size: 1.25em;
                font-weight: 700;
                letter-spacing: -0.02em;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                padding-bottom: 15px;
                width: 100%;
            }
            .stat-card p {
                margin: 0;
                line-height: 1.6;
                color: #cbd5e1;
                font-size: 0.95em;
            }
            .stat-card p b, .stat-card p strong {
                color: #ffffff;
                font-weight: 600;
            }
            .highlight-text {
                color: #4dd7a8;
                font-weight: 700;
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
