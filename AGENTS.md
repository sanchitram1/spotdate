# AGENTS.md

## Project Overview

**spotdate** is a music-based dating application (IEOR 243, UC Berkeley) that
matches people based on shared listening histories and music consumption
patterns. The core of this repo is an ML training pipeline that extracts
user-level features from listening data, generates synthetic match labels, trains
models, and evaluates match quality.

## Project Structure

```
training/                  # ML pipeline (see training/README.md)
├── slice.py               # Temporal split: past vs future listening history
├── feature_extraction/    # User-level feature engineering (see training/feature_extraction/README.md)
│   ├── main.py            # Orchestrator — the only entrypoint needed
│   ├── _contract.py       # FeatureExtractor protocol + EXPECTED_COLUMNS
│   └── extractors/        # One module per feature family (see training/feature_extraction/extractors/README.md)
├── labeling/              # Synthetic label generation (see training/labeling/README.md)
│   ├── heuristics.py      # Hipster-overlap pairwise scoring
│   └── clustering.py      # KMeans cluster-distribution cosine similarity
├── models/                # Training notebooks (autoencoder, siamese)
├── evaluation.py          # Unified Top-K Jaccard evaluation across all models
├── eda/                   # Exploratory data analysis notebooks
data-loading/              # Dataset ingestion scripts & notebooks (see data-loading/README.md)
data/                      # Local CSV artifacts (listening histories, features, edgelists)
scripts/                   # Utility scripts (GCS sync, etc.)
utils/                     # Shared utilities (logger)
tests/                     # pytest tests
```

## Development Setup & Tooling

- **Python 3.13**, managed with [uv](https://docs.astral.sh/uv/)
- **Formatter/linter**: `ruff` — run before committing:
  ```bash
  uv run ruff format /path/to/directory/or/file
  uv run ruff check  /path/to/directory/or/file --fix
  ```
- **CI** (`.github/workflows/ci.yml`): runs `ruff format --check` and
  `ruff check` on every push/PR to `main`
- **CSV delimiter is `;`** (not `,`) — inherited from the MusicBrainz data
  source. All `pd.read_csv` calls must use `delimiter=";"`.

## Architectural Constraints & Non-Negotiables

### Temporal split is sacred

`slice.py` **must** run first in the pipeline. It splits raw listening history
into two sets:

- **`past_listening_history`** — used for feature extraction and model training
- **`future_listening_history`** — used **only** for label generation

**Never train on future data.** Never generate labels from past data. The split
ensures we measure alignment on data the model has never seen.

### Cutoff timestamp must stay in sync

The cutoff `2012-03-26 13:30:08+00:00` appears in three places:

- `training/slice.py` → `SliceConfig.cutoff_timestamp`
- `training/labeling/heuristics.py` → `CUTOFF_TIMESTAMP`
- `training/feature_extraction/main.py` → `CUTOFF_TIMESTAMP`

If this value changes, it **must** be updated in all three locations.

### Feature extractor contract

All feature modules must implement the `FeatureExtractor` protocol defined in
`training/feature_extraction/_contract.py`:

```python
def __call__(self, listening_history: pd.DataFrame) -> pd.DataFrame: ...
```

- **Input**: raw listening history with at least the columns in
  `EXPECTED_COLUMNS`
- **Output**: a DataFrame **keyed by `user_id`** containing only feature columns
  for that family

### Column naming convention

Each extractor family prefixes its columns to avoid collisions:

| Module | Prefix |
|--------|--------|
| `basic.py` | `total_*`, `n_unique_*`, `avg_*`, `genre_*` |
| `temporal.py` | `temporal_*` |
| `genre.py` | `genre_*` |
| `audio_features.py` | `audio_*` |
| `album.py` | `album_*` |
| `artist.py` | `artist_*` |

New feature families must follow this pattern.

### `features_df.csv` is the canonical feature table

- One row per user, indexed by `user_id`
- All columns numeric or well-defined categorical encodings
- Downstream labeling and model training treat this as the **single source of
  truth** for user features

### Edgelist schema

All labeling outputs must produce DataFrames with these columns:

- **Heuristics** (`heuristics.py`): `user_id_anchor`, `user_id_positive`,
  `match_score`
- **Clustering** (`clustering.py`): `user_anchor`, `user_match`,
  `similarity_score`

### Secrets and configuration

All credentials and environment-specific values come from `.env` or environment
variables. Never hardcode secrets in source code.

## Pipeline Execution Order

```
1. data-loading/         → Ingest raw datasets into data/
2. training/slice.py     → Split into past + future listening history
3. training/feature_extraction/main.py  → Extract features from PAST data → features_df.csv
4. training/labeling/    → Generate match labels from FUTURE data → edgelist CSVs
5. training/models/      → Train models using features + labels
6. training/evaluation.py → Evaluate model predictions against ground-truth edgelists
```

## Component Documentation

Each major component has its own README with detailed instructions:

- **Training pipeline overview**: [`training/README.md`](training/README.md)
- **Feature extraction**: [`training/feature_extraction/README.md`](training/feature_extraction/README.md)
- **Feature catalog**: [`training/feature_extraction/extractors/README.md`](training/feature_extraction/extractors/README.md)
- **Labeling**: [`training/labeling/README.md`](training/labeling/README.md)
- **Data loading**: [`data-loading/README.md`](data-loading/README.md)

