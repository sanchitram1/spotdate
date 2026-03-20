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

_EDGELIST_COLS = ["user_anchor", "user_match", "similarity_score"]


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
    cutoff_score: float = 0.99


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
        "--listening-history",
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
    _require_columns(tracks_df, config.feature_cols, df_name="tracks")

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
    *,
    scaler: StandardScaler,
    kmeans: KMeans,
    config: ClusterConfig,
    agg_config: AggregateConfig,
) -> pd.DataFrame:
    """Aggregate listening history into per-user cluster distribution vectors.

    Uses the fitted scaler and kmeans to predict clusters directly on the
    listening history feature columns, avoiding a join on track_mbid.
    """
    _require_columns(
        listening_history_df, ("user_id", *config.feature_cols), df_name="history"
    )

    before = len(listening_history_df)
    merged = listening_history_df.dropna(subset=list(config.feature_cols)).copy()
    dropped = before - len(merged)
    if dropped:
        logger.warning("Dropped %d history rows with missing features.", dropped)

    X = merged.loc[:, list(config.feature_cols)]
    merged["cluster"] = kmeans.predict(scaler.transform(X))

    logger.info("Predicted clusters for %d listening history rows.", len(merged))

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

    if user_cluster_dist.shape[0] < agg_config.top_k + 1:
        logger.warning(
            "Only %d users available; cannot produce %d matches per user.",
            user_cluster_dist.shape[0],
            agg_config.top_k,
        )

    return user_cluster_dist


def _compute_similarity(
    user_vectors: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray]:
    """Return (user_ids, similarity_matrix) with self-similarity zeroed out."""
    user_ids = user_vectors.index.to_numpy()
    sim = cosine_similarity(user_vectors.to_numpy())
    np.fill_diagonal(sim, -np.inf)
    return user_ids, sim


def build_full_edgelist(user_ids: np.ndarray, sim: np.ndarray) -> pd.DataFrame:
    """Every ordered (i, j) pair where i != j."""
    n = len(user_ids)
    if n < 2:
        return pd.DataFrame(columns=_EDGELIST_COLS)

    row_idx, col_idx = np.where(np.ones((n, n), dtype=bool) & ~np.eye(n, dtype=bool))
    return pd.DataFrame(
        {
            "user_anchor": user_ids[row_idx],
            "user_match": user_ids[col_idx],
            "similarity_score": sim[row_idx, col_idx],
        }
    )


def build_topk_edgelist(
    user_ids: np.ndarray, sim: np.ndarray, *, top_k: int
) -> pd.DataFrame:
    n_users = sim.shape[0]
    k = min(top_k, max(0, n_users - 1))
    if k == 0:
        return pd.DataFrame(columns=_EDGELIST_COLS)

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


def build_high_scores_edgelist(
    user_ids: np.ndarray, sim: np.ndarray, *, cutoff_score: float
) -> pd.DataFrame:
    """Only pairs whose similarity is strictly above the cutoff."""
    n = len(user_ids)
    if n < 2:
        return pd.DataFrame(columns=_EDGELIST_COLS)

    mask = sim > cutoff_score
    row_idx, col_idx = np.where(mask)
    return pd.DataFrame(
        {
            "user_anchor": user_ids[row_idx],
            "user_match": user_ids[col_idx],
            "similarity_score": sim[row_idx, col_idx],
        }
    )


def main() -> None:
    args = parse_args()

    if not args.no_save and not args.output:
        raise SystemExit("--output is required unless --no-save is specified.")

    tracks_path = Path(args.tracks)
    history_path = Path(args.listening_history)

    logger.info("Reading tracks from %s", tracks_path)
    tracks = pd.read_csv(tracks_path)

    logger.info("Reading listening history from %s", history_path)
    history = pd.read_csv(history_path, delimiter=";")

    logger.info("tracks shape: %s", tracks.shape)
    logger.info("history shape: %s", history.shape)

    cluster_config = ClusterConfig()
    aggregate_config = AggregateConfig()

    _tracks_with_cluster, scaler, kmeans = cluster_tracks(tracks, config=cluster_config)

    user_vectors = aggregate_users(
        history,
        scaler=scaler,
        kmeans=kmeans,
        config=cluster_config,
        agg_config=aggregate_config,
    )

    expected_users = set(history["user_id"].unique())
    actual_users = set(user_vectors.index)
    missing_users = expected_users - actual_users
    if missing_users:
        raise ValueError(
            f"{len(missing_users)} users from listening history have no cluster "
            f"vectors (likely all feature rows were NaN). Examples: "
            f"{sorted(missing_users)[:5]}"
        )

    user_ids, sim = _compute_similarity(user_vectors)
    edgelist_topk = build_topk_edgelist(user_ids, sim, top_k=aggregate_config.top_k)
    edgelist_full = build_full_edgelist(user_ids, sim)
    edgelist_high_scores = build_high_scores_edgelist(
        user_ids, sim, cutoff_score=aggregate_config.cutoff_score
    )

    logger.info(
        "Edgelist sizes: topk=%d full=%d high_scores=%d",
        len(edgelist_topk),
        len(edgelist_full),
        len(edgelist_high_scores),
    )

    if args.no_save:
        logger.info("No save: here's the top 10 edgelist output")
        print(edgelist_topk.head(10))
        return

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    for name, df in (
        (f"edgelist_top{aggregate_config.top_k}", edgelist_topk),
        ("edgelist_full", edgelist_full),
        ("edgelist_high_scores", edgelist_high_scores),
    ):
        path = output_dir / f"{name}.csv"
        logger.info("Writing %s (%d rows) to %s", name, len(df), path)
        df.to_csv(path, index=False)

    logger.info("Done.")


if __name__ == "__main__":
    main()
