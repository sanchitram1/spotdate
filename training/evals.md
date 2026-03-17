---
name: TopK evaluation module
overview: Add a reusable, notebook-friendly evaluation module that compares model Top‑K neighbors (from a similarity matrix) against Top‑K ground-truth neighbors (from an edgelist), restricting evaluation to the shared user universe and producing per-user Jaccard + summary stats + plotting helpers.
todos:
  - id: design-api
    content: Define evaluation module API and input contracts (similarity_df + edgelist columns + undirected handling).
    status: pending
  - id: implement-topk
    content: Implement Top‑K extraction from similarity + Top‑K truth from edgelist restricted to similarity_df universe.
    status: pending
  - id: metrics-and-summary
    content: Implement per-user Jaccard, thresholds (including 1/(2K-1)), and summary statistics.
    status: pending
  - id: plotting
    content: Add optional matplotlib plotting helper for Jaccard distribution and threshold overlays.
    status: pending
  - id: notebook-integration
    content: Document minimal notebook call pattern (no file I/O in evaluation module).
    status: pending
isProject: false
---

## Goal

Create a small evaluation layer that you can call from any training notebook:

- Takes in-memory objects only (no CSV reads).
- Standardizes to the evaluation universe (users present in `similarity_df`).
- Builds **Top‑K predicted neighbors** from `similarity_df`.
- Builds **Top‑K ground-truth neighbors** per user from `edgelist` using `match_score`.
- Computes per-user **Jaccard** (directionless) and summary/distribution outputs.

## Where it should live

- New module: `[training/evaluation.py](training/evaluation.py)`
- Notebook imports it (e.g. `from training.evaluation import evaluate_topk`)

## Core data contracts (inputs)

- **Similarity input**: `similarity_df: pd.DataFrame` square, index==columns user ids.
- **Edgelist input**: `edgelist: pd.DataFrame` with configurable column names.
  - Defaults should support both patterns already in repo/notebooks:
    - (`user_1`, `user_2`, optional score)
    - (`user_id_anchor`, `user_id_positive`, `match_score`) from `[training/labeling/heuristics.py](training/labeling/heuristics.py)`.

## Public API (functions)

- `normalize_similarity(similarity_df) -> (ids: np.ndarray, S: np.ndarray)`
  - Validates square/index/columns alignment.
  - Converts to NumPy and sets diagonal to `-inf` once.
- `topk_from_similarity(similarity_df, *, k: int) -> dict[user_id, np.ndarray[user_id]]`
  - Uses `np.argpartition` to compute Top‑K neighbors per user efficiently.
  - Returns neighbors as user ids (not indices) so downstream code is column-name agnostic.
- `topk_from_edgelist(edgelist, *, universe: pd.Index, k: int, anchor_col: str, other_col: str, score_col: str | None, undirected: bool=True) -> dict[user_id, np.ndarray[user_id]]`
  - **Universe restriction**: keep only rows where both endpoints are in `universe`.
  - If `undirected=True`, treat each edge as contributing to both endpoints’ neighbor lists.
  - **Ranking**:
    - If `score_col` provided: sort by that descending.
    - Else: use frequency (groupby count) as a fallback score.
  - Emits exactly up to K neighbors per user (some users may have <K).
- `jaccard_topk(pred: dict, truth: dict, *, k: int, min_truth_neighbors: int=1) -> pd.DataFrame`
  - Produces per-user metrics:
    - `user_id`
    - `pred_k` (len of predicted set)
    - `truth_k` (len of truth set)
    - `intersection`
    - `union`
    - `jaccard`
    - `has_any_overlap` (intersection>0)
  - **Note on your “1/19”**: if both sides are size K=10, then “≥1 overlap” implies Jaccard ≥ 1/(2K-1)=1/19.
    - Implement this threshold helper: `any_overlap_jaccard_threshold(k) -> float`.
- `summarize_jaccard(df, *, thresholds: Iterable[float]) -> dict`
  - Returns high-signal summary stats for re-use across models:
    - counts, coverage (how many users evaluated), median/p75/p90
    - `% above threshold` for each threshold
- `plot_jaccard_distribution(df, *, bins=50, ax=None) -> matplotlib.axes.Axes`
  - Simple histogram (optionally overlay vertical lines for thresholds).
  - Keep plotting optional so the module is usable in non-notebook contexts.

## Evaluation flow (what `evaluate_topk(...)` does)

Add a convenience wrapper function:

- `evaluate_topk(similarity_df, edgelist, *, k=10, undirected=True, anchor_col=..., other_col=..., score_col=..., thresholds=(1/(2k-1), 0.1, 0.2, 0.3)) -> (per_user_df, summary)`

Steps inside:

1. **Set evaluation universe**: `universe = similarity_df.index` (your requirement: “everything in similarity_df”).
2. **Predicted Top‑K**: compute once from `similarity_df`.
3. **Truth Top‑K**: filter `edgelist` down to `universe`, then select Top‑K per user by score (or frequency).
4. **Per-user Jaccard**: compute metrics + `has_any_overlap`.
5. **Summary + plot-ready outputs**.

## Notebook usage pattern (intended)

In `[training/Rox_Autoencoder.ipynb](training/Rox_Autoencoder.ipynb)` (and future notebooks):

- You keep loading/constructing `edgelist` and `similarity_df` in the notebook.
- Call:
  - `per_user, summary = evaluate_topk(similarity_df, edgelist, k=10, undirected=True, anchor_col="user_id_anchor", other_col="user_id_positive", score_col="match_score")`
  - then `plot_jaccard_distribution(per_user)`.

## Implementation notes / performance

- Predicted Top‑K should stay O(n^2) memory only for the similarity matrix you already have; Top‑K extraction is O(n*K) additional.
- Truth Top‑K on 15.9M rows must avoid Python loops:
  - Filter to universe first.
  - If undirected, concatenate a swapped copy to represent both directions.
  - Use groupby aggregate for score (sum/mean/max or count), then sort+groupby.head(k).

## Files to touch

- Add `[training/evaluation.py](training/evaluation.py)` only.
- (Optional, later) a tiny call-site cell in notebooks for usage; not required for module correctness.

