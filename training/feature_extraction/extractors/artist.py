#!/usr/bin/env pkgx uv run
import numpy as np
import pandas as pd

from utils.logger import get_logger

logger = get_logger("feature_extraction.artist", 20)


def _gini(array: np.ndarray) -> float:
    """Gini coefficient on a count vector. High = unequal (top-heavy)."""
    array = np.array(array, dtype=float)
    if array.size == 0:
        return 0.0
    if np.amin(array) < 0:
        array = array - np.amin(array)
    array = array + 1e-12
    array = np.sort(array)
    index = np.arange(1, array.shape[0] + 1)
    n = array.shape[0]
    return float(np.sum((2 * index - n - 1) * array) / (n * np.sum(array)))


def _genre_mode(series: pd.Series) -> str:
    """Most frequent genre in series; empty string if none."""
    if series.empty:
        return ""
    modes = series.mode()
    return str(modes.iloc[0]) if len(modes) else ""


def _build_artist_grouped_df(listening_history: pd.DataFrame) -> pd.DataFrame:
    """Build artist-level aggregates: artist_mbid, artist_name (if present), artist_genre (mode), global_listen_count, global_rank."""
    required = ["artist_mbid", "genre"]
    if not all(c in listening_history.columns for c in required):
        return pd.DataFrame()

    count_df = (
        listening_history.groupby("artist_mbid", as_index=False).size().rename(columns={"size": "global_listen_count"})
    )
    genre_df = (
        listening_history.groupby("artist_mbid")["genre"]
        .apply(_genre_mode, include_groups=False)
        .reset_index(name="artist_genre")
    )
    grouped = count_df.merge(genre_df, on="artist_mbid", how="left")
    if "artist_name" in listening_history.columns:
        name_df = (
            listening_history.groupby("artist_mbid")["artist_name"]
            .first()
            .reset_index()
        )
        grouped = grouped.merge(name_df, on="artist_mbid", how="left")
    grouped = grouped.sort_values("global_listen_count", ascending=False).reset_index(drop=True)
    grouped["global_rank"] = np.arange(1, len(grouped) + 1, dtype=np.int64)
    return grouped


def extract(listening_history: pd.DataFrame) -> pd.DataFrame:
    """
    Artist-level user features.

    Input: raw listening_history with user_id, artist_mbid, genre (artist_name optional).
    Output: dataframe indexed by user_id with nunique_artist, artist_concentration_index,
    one_hit_wonder, hipster_gap, artist_entropy.
    """
    logger.info("Extracting artist features...")

    if listening_history is None or listening_history.empty:
        return pd.DataFrame(index=pd.Index([], name="user_id"))

    df = listening_history.dropna(subset=["user_id", "artist_mbid"]).copy()
    if df.empty:
        user_ids = listening_history["user_id"].dropna().unique()
        out = pd.DataFrame(
            index=pd.Index(user_ids, name="user_id"),
            columns=[
                "nunique_artist",
                "artist_concentration_index",
                "one_hit_wonder",
                "hipster_gap",
                "artist_entropy",
            ],
        )
        return out.fillna(0)

    artist_grouped_df = _build_artist_grouped_df(df)
    user_artist_counts = (
        df.groupby(["user_id", "artist_mbid"]).size().reset_index(name="listen_count")
    )

    # nunique_artist
    nunique = (
        user_artist_counts.groupby("user_id")["artist_mbid"]
        .nunique()
        .reset_index(name="nunique_artist")
    )

    # artist_concentration_index (Gini of per-artist listen counts per user)
    def gini_per_user(g):
        return _gini(g["listen_count"].values)

    concentration = (
        user_artist_counts.groupby("user_id")
        .apply(gini_per_user, include_groups=False)
        .reset_index(name="artist_concentration_index")
    )
    concentration.columns = ["user_id", "artist_concentration_index"]

    # one_hit_wonder: (artists with count 1) / total artists
    n_artists = user_artist_counts.groupby("user_id").size().reset_index(name="n_artists")
    n_one_hit = (
        user_artist_counts[user_artist_counts["listen_count"] == 1]
        .groupby("user_id")
        .size()
        .reset_index(name="n_one_hit")
    )
    one_hit = n_artists.merge(n_one_hit, on="user_id", how="left").fillna(0)
    one_hit["one_hit_wonder"] = np.where(
        one_hit["n_artists"] > 0,
        one_hit["n_one_hit"] / one_hit["n_artists"],
        0.0,
    )
    one_hit = one_hit[["user_id", "one_hit_wonder"]]

    # favorite artist per user (artist with max listen count; tie-break by first)
    favorite = (
        user_artist_counts.sort_values(["user_id", "listen_count", "artist_mbid"], ascending=[True, False, True])
        .groupby("user_id", as_index=False)
        .first()[["user_id", "artist_mbid"]]
        .rename(columns={"artist_mbid": "favorite_artist_mbid"})
    )
    # hipster_gap: max(0, global_rank of favorite - 10)
    rank_df = artist_grouped_df[["artist_mbid", "global_rank"]].rename(
        columns={"artist_mbid": "favorite_artist_mbid"}
    )
    hipster = favorite.merge(rank_df, on="favorite_artist_mbid", how="left")
    hipster["hipster_gap"] = np.maximum(
        0, hipster["global_rank"].fillna(np.inf).astype(float) - 10
    )
    hipster = hipster[["user_id", "hipster_gap"]]

    # artist_entropy: distinct genres among user's artists, normalized by log(n_artists + 1)
    artist_to_genre = artist_grouped_df[["artist_mbid", "artist_genre"]].drop_duplicates()
    user_artists = user_artist_counts[["user_id", "artist_mbid"]].drop_duplicates()
    user_genres = user_artists.merge(artist_to_genre, on="artist_mbid", how="left")
    user_genres["artist_genre"] = user_genres["artist_genre"].fillna("").astype(str)
    distinct_genres = (
        user_genres.groupby("user_id")["artist_genre"]
        .nunique()
        .reset_index(name="distinct_genre_count")
    )
    n_artists_per_user = user_artist_counts.groupby("user_id")["artist_mbid"].nunique().reset_index(name="n_artists")
    entropy_df = distinct_genres.merge(n_artists_per_user, on="user_id", how="left")
    entropy_df["artist_entropy"] = np.where(
        entropy_df["n_artists"] > 0,
        entropy_df["distinct_genre_count"] / np.log(entropy_df["n_artists"] + 1),
        0.0,
    )
    artist_entropy_out = entropy_df[["user_id", "artist_entropy"]]

    # join all features; index by user_id
    result = nunique.merge(concentration, on="user_id", how="outer")
    result = result.merge(one_hit, on="user_id", how="outer")
    result = result.merge(hipster, on="user_id", how="outer")
    result = result.merge(artist_entropy_out, on="user_id", how="outer")

    # ensure all users from original history have a row
    all_users = pd.DataFrame({"user_id": df["user_id"].unique()})
    result = all_users.merge(result, on="user_id", how="left")
    result = result.set_index("user_id", drop=True)
    result.index.name = "user_id"
    return result.fillna(0)
