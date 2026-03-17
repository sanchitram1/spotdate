#!/usr/bin/env pkgx uv run

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler

from utils.logger import get_logger

logger = get_logger("clustering", 20)


@dataclass(frozen=True)
class ClusterConfig:
    feature_cols: tuple[str, ...] = (
        "danceability",
        "energy",
        "tempo",
        "valence",
        "acousticness",
        "instrumentalness",
        "liveness",
        "speechiness",
        "loudness",
    )
    n_clusters: int = 12
    random_state: int = 42
    n_init: int = 10


@dataclass(frozen=True)
class AggregateConfig:
    top_k: int = 10


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Cluster tracks into KMeans clusters, aggregate users into cluster "
            "distributions, then emit a user-user edgelist of top-k cosine "
            "similarity matches."
        ),
    )
    parser.add_argument("--tracks", required=True, help="Path to the tracks CSV.")
    parser.add_argument(
        "--listening_history",
        required=True,
        help=(
            "Path to the listening history CSV (must include user_id and track_mbid)."
        ),
    )
    parser.add_argument(
        "--output",
        help="Directory where edgelist.csv will be written (required unless --no-save).",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Do not write files; print edgelist CSV to stdout.",
    )
    return parser.parse_args()


def _require_columns(
    df: pd.DataFrame, required: Iterable[str], *, df_name: str
) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"{df_name} missing required columns: {missing}")


def cluster_tracks(
    tracks_df: pd.DataFrame, *, config: ClusterConfig
) -> tuple[pd.DataFrame, StandardScaler, KMeans]:
    """Fit a KMeans model on track features and return tracks with cluster labels."""
    _require_columns(tracks_df, ("track_mbid", *config.feature_cols), df_name="tracks")

    before = len(tracks_df)
    tracks_df = tracks_df.dropna(subset=list(config.feature_cols)).copy()
    dropped = before - len(tracks_df)
    if dropped:
        logger.warning("Dropped %d tracks with missing features.", dropped)

    X = tracks_df.loc[:, list(config.feature_cols)].copy()
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    kmeans = KMeans(
        n_clusters=config.n_clusters,
        random_state=config.random_state,
        n_init=config.n_init,
    )
    tracks_df["cluster"] = kmeans.fit_predict(X_scaled)

    logger.info(
        "KMeans fit complete. n_clusters=%d random_state=%d n_init=%d",
        config.n_clusters,
        config.random_state,
        config.n_init,
    )

    return tracks_df, scaler, kmeans


def aggregate_users(
    listening_history_df: pd.DataFrame,
    track_cluster_map: pd.DataFrame,
    *,
    config: AggregateConfig,
) -> pd.DataFrame:
    """Aggregate listening history into per-user cluster distribution vectors.

    This stays separate because the current approach is intentionally simple and
    we expect to improve/replace it later.
    """
    _require_columns(listening_history_df, ("user_id", "track_mbid"), df_name="history")
    _require_columns(track_cluster_map, ("track_mbid", "cluster"), df_name="track_map")

    merged = listening_history_df.merge(
        track_cluster_map.drop_duplicates(subset=["track_mbid"]),
        on="track_mbid",
        how="left",
    )

    matched = int(merged["cluster"].notna().sum())
    unmatched = int(merged["cluster"].isna().sum())
    logger.info(
        "Merged history with clusters. matched=%d unmatched=%d", matched, unmatched
    )

    merged = merged.dropna(subset=["cluster"]).copy()
    merged["cluster"] = merged["cluster"].astype(int)

    user_cluster_counts = (
        merged.groupby(["user_id", "cluster"]).size().unstack(fill_value=0)
    )
    user_cluster_dist = user_cluster_counts.div(
        user_cluster_counts.sum(axis=1), axis=0
    ).fillna(0.0)

    logger.info(
        "Built user cluster distributions. users=%d clusters=%d",
        user_cluster_dist.shape[0],
        user_cluster_dist.shape[1],
    )

    if user_cluster_dist.shape[0] < config.top_k + 1:
        logger.warning(
            "Only %d users available; cannot produce %d matches per user.",
            user_cluster_dist.shape[0],
            config.top_k,
        )

    return user_cluster_dist


def build_topk_edgelist(user_vectors: pd.DataFrame, *, top_k: int) -> pd.DataFrame:
    if user_vectors.empty:
        return pd.DataFrame(columns=["user_anchor", "user_match", "similarity_score"])

    user_ids = user_vectors.index.to_numpy()
    sim = cosine_similarity(user_vectors.to_numpy())
    np.fill_diagonal(sim, -np.inf)

    n_users = sim.shape[0]
    k = min(top_k, max(0, n_users - 1))
    if k == 0:
        return pd.DataFrame(columns=["user_anchor", "user_match", "similarity_score"])

    edges: list[dict[str, object]] = []
    for i in range(n_users):
        row = sim[i]
        candidate_idx = np.argpartition(-row, kth=k - 1)[:k]
        candidate_idx = candidate_idx[np.argsort(-row[candidate_idx])]

        for j in candidate_idx:
            edges.append(
                {
                    "user_anchor": user_ids[i],
                    "user_match": user_ids[j],
                    "similarity_score": float(row[j]),
                }
            )

    return pd.DataFrame(edges)


def main() -> None:
    args = parse_args()

    if not args.no_save and not args.output:
        raise SystemExit("--output is required unless --no-save is specified.")

    tracks_path = Path(args.tracks)
    history_path = Path(args.listening_history)

    logger.info("Reading tracks from %s", tracks_path)
    tracks = pd.read_csv(tracks_path)

    logger.info("Reading listening history from %s", history_path)
    history = pd.read_csv(history_path)

    logger.info("tracks shape: %s", tracks.shape)
    logger.info("history shape: %s", history.shape)

    cluster_config = ClusterConfig()
    aggregate_config = AggregateConfig()

    tracks_with_cluster, _scaler, _kmeans = cluster_tracks(
        tracks, config=cluster_config
    )
    track_cluster_map = tracks_with_cluster.loc[:, ["track_mbid", "cluster"]].copy()

    user_vectors = aggregate_users(history, track_cluster_map, config=aggregate_config)
    edgelist = build_topk_edgelist(user_vectors, top_k=aggregate_config.top_k)

    if args.no_save:
        print(edgelist.to_csv(index=False))
        return

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "edgelist.csv"
    logger.info("Writing edgelist to %s", output_path)
    edgelist.to_csv(output_path, index=False)
    logger.info("Done.")


if __name__ == "__main__":
    main()
