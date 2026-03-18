"""Top-K evaluation: compare predicted neighbors (from a similarity matrix)
against ground-truth neighbors (from an edgelist) using per-user Jaccard."""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    import matplotlib.axes


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def any_overlap_jaccard_threshold(k: int) -> float:
    """Minimum Jaccard when both sets are size *k* and share ≥1 element.

    ``1 / (2*k - 1)``
    """
    return 1.0 / (2 * k - 1)


# ---------------------------------------------------------------------------
# Similarity matrix utilities
# ---------------------------------------------------------------------------


def normalize_similarity(
    similarity_df: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray]:
    """Validate a square similarity DataFrame and return (ids, S).

    * Checks that index == columns (same order).
    * Sets the diagonal to ``-inf`` so a user is never their own neighbor.

    Returns
    -------
    ids : np.ndarray
        User ids taken from ``similarity_df.index``.
    S : np.ndarray
        2-D float array with diagonal set to ``-inf``.
    """
    if similarity_df.shape[0] != similarity_df.shape[1]:
        raise ValueError(
            f"similarity_df must be square, got shape {similarity_df.shape}"
        )
    if not similarity_df.index.equals(similarity_df.columns):
        raise ValueError("similarity_df.index and .columns must be identical")

    ids = similarity_df.index.to_numpy()
    S = similarity_df.to_numpy(dtype=float, copy=True)
    np.fill_diagonal(S, -np.inf)
    return ids, S


# ---------------------------------------------------------------------------
# Top-K extraction
# ---------------------------------------------------------------------------


def topk_from_similarity(
    similarity_df: pd.DataFrame,
    *,
    k: int,
) -> dict:
    """Return top-*k* predicted neighbors per user from a similarity matrix.

    Uses ``np.argpartition`` for O(n·K) extraction per row.

    Returns
    -------
    dict[user_id, np.ndarray[user_id]]
    """
    ids, S = normalize_similarity(similarity_df)
    n = len(ids)
    actual_k = min(k, n - 1)
    if actual_k <= 0:
        return {uid: np.array([], dtype=ids.dtype) for uid in ids}

    result: dict = {}
    for i in range(n):
        row = S[i]
        part_idx = np.argpartition(-row, kth=actual_k - 1)[:actual_k]
        part_idx = part_idx[np.argsort(-row[part_idx])]
        result[ids[i]] = ids[part_idx]
    return result


def topk_from_edgelist(
    edgelist: pd.DataFrame,
    *,
    universe: pd.Index,
    k: int,
    anchor_col: str = "user_id_anchor",
    other_col: str = "user_id_positive",
    score_col: str | None = "match_score",
    undirected: bool = True,
) -> dict:
    """Return top-*k* ground-truth neighbors per user from an edgelist.

    Parameters
    ----------
    edgelist : pd.DataFrame
        Must contain ``anchor_col`` and ``other_col`` (and optionally
        ``score_col``).
    universe : pd.Index
        Only edges with **both** endpoints in *universe* are kept.
    k : int
        Maximum neighbors per user.
    score_col : str | None
        Column used to rank neighbors (descending).  When ``None``, raw
        frequency (count of edges) is used instead.
    undirected : bool
        If ``True`` each edge contributes to both endpoints' neighbor lists.
    """
    cols = [anchor_col, other_col] + ([score_col] if score_col else [])
    df = edgelist.reset_index()[cols].copy()

    # Universe restriction – both endpoints must be present.
    mask = df[anchor_col].isin(universe) & df[other_col].isin(universe)
    df = df.loc[mask]

    # Standardize column names for internal processing.
    rename = {anchor_col: "_anchor", other_col: "_other"}
    if score_col:
        rename[score_col] = "_score"
    df = df.rename(columns=rename)

    if undirected:
        swapped = df.rename(columns={"_anchor": "_other", "_other": "_anchor"})
        df = pd.concat([df, swapped], ignore_index=True)

    if score_col:
        # When a pair appears multiple times, take the max score.
        df = df.groupby(["_anchor", "_other"], sort=False)["_score"].max().reset_index()
        df = df.sort_values(["_anchor", "_score"], ascending=[True, False])
    else:
        # Use frequency as the ranking signal.
        df = (
            df.groupby(["_anchor", "_other"], sort=False)
            .size()
            .reset_index(name="_score")
        )
        df = df.sort_values(["_anchor", "_score"], ascending=[True, False])

    topk = df.groupby("_anchor").head(k)

    result: dict = {}
    for anchor, grp in topk.groupby("_anchor"):
        result[anchor] = grp["_other"].to_numpy()

    return result


# ---------------------------------------------------------------------------
# Jaccard
# ---------------------------------------------------------------------------


def jaccard_topk(
    pred: dict,
    truth: dict,
    *,
    k: int,
    min_truth_neighbors: int = 1,
) -> pd.DataFrame:
    """Per-user Jaccard between predicted and ground-truth neighbor sets.

    Only users present in *both* ``pred`` and ``truth`` (with at least
    ``min_truth_neighbors`` truth neighbors) are included.

    Returns a DataFrame with columns:
        user_id, pred_k, truth_k, intersection, union, jaccard, has_any_overlap
    """
    rows: list[dict] = []
    common_users = set(pred) & set(truth)
    for uid in common_users:
        p = set(pred[uid])
        t = set(truth[uid])
        if len(t) < min_truth_neighbors:
            continue
        inter = len(p & t)
        union = len(p | t)
        jacc = inter / union if union else 0.0
        rows.append(
            {
                "user_id": uid,
                "pred_k": len(p),
                "truth_k": len(t),
                "intersection": inter,
                "union": union,
                "jaccard": jacc,
                "has_any_overlap": inter > 0,
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


def summarize_jaccard(
    df: pd.DataFrame,
    *,
    thresholds: Iterable[float] = (),
) -> dict:
    """High-signal summary statistics from the per-user Jaccard DataFrame."""
    n = len(df)
    if n == 0:
        return {"n_users": 0}

    jaccard = df["jaccard"]
    summary: dict = {
        "n_users": n,
        "median": float(jaccard.median()),
        "mean": float(jaccard.mean()),
        "p75": float(jaccard.quantile(0.75)),
        "p90": float(jaccard.quantile(0.90)),
        "pct_any_overlap": float(df["has_any_overlap"].mean()),
    }
    for t in thresholds:
        summary[f"pct_above_{t:.4f}"] = float((jaccard >= t).mean())
    return summary


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------


def plot_jaccard_distribution(
    df: pd.DataFrame,
    *,
    bins: int = 50,
    thresholds: Iterable[float] = (),
    ax: matplotlib.axes.Axes | None = None,
) -> matplotlib.axes.Axes:
    """Histogram of per-user Jaccard with optional threshold lines."""
    import matplotlib.pyplot as plt

    if ax is None:
        _, ax = plt.subplots()

    ax.hist(df["jaccard"], bins=bins, edgecolor="black", alpha=0.7)
    for t in thresholds:
        ax.axvline(t, color="red", linestyle="--", label=f"threshold={t:.4f}")
    ax.set_xlabel("Jaccard")
    ax.set_ylabel("# users")
    ax.set_title("Per-user Jaccard distribution")
    if thresholds:
        ax.legend()
    return ax


# ---------------------------------------------------------------------------
# Convenience wrapper
# ---------------------------------------------------------------------------


def evaluate_topk(
    similarity_df: pd.DataFrame,
    edgelist: pd.DataFrame,
    *,
    k: int = 10,
    undirected: bool = True,
    anchor_col: str = "user_id_anchor",
    other_col: str = "user_id_positive",
    score_col: str | None = "match_score",
    thresholds: tuple[float, ...] | None = None,
    min_truth_neighbors: int = 1,
) -> tuple[pd.DataFrame, dict]:
    """End-to-end Top-K evaluation.

    Returns
    -------
    per_user : pd.DataFrame
        Per-user Jaccard metrics.
    summary : dict
        Aggregate statistics including threshold coverage.
    """
    if thresholds is None:
        t0 = any_overlap_jaccard_threshold(k)
        thresholds = (t0, 0.1, 0.2, 0.3)

    universe = similarity_df.index

    pred = topk_from_similarity(similarity_df, k=k)
    truth = topk_from_edgelist(
        edgelist,
        universe=universe,
        k=k,
        anchor_col=anchor_col,
        other_col=other_col,
        score_col=score_col,
        undirected=undirected,
    )

    missing = set(pred) - set(truth)
    if missing:
        print(
            f"WARNING: {len(missing)} user(s) in similarity_df have no ground-truth edges "
            f"in the edgelist (after universe filtering). Examples: "
            f"{sorted(missing)[:5]}"
        )

    per_user = jaccard_topk(pred, truth, k=k, min_truth_neighbors=min_truth_neighbors)
    summary = summarize_jaccard(per_user, thresholds=thresholds)

    return per_user, summary
