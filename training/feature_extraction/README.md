# Feature extraction

This module is responsible for **turning raw listening history + track metadata
into a clean, user-level feature table** that downstream models can train on.

## Getting Setup

### Pre-requisites:

- You need a data directory at the root, with the file `past_listening_history.csv`. This
  file contains user level listening history, for periods before our cutoff date.
  data, merged with the track level metadata
- [uv](https://astral.sh/uv) for dependency management / running python files

### Running locally

Use the orchestrator to smoke-test a feature group end-to-end.

- **Required flags**: you must provide **both** `--input` and `--output`.
- **Run only one feature group and print the result**:

```bash
uv run training/feature_extraction/main.py \
  --input data/naive-sample-subset.csv \
  --output data/test.csv \
  --only temporal \
  --print
```

At a high level:
- **Input**: user–track interaction logs (listening history) and track-level
  metadata
(genres, audio features, album and artist info).
- **Output**: `features_df.csv`, where:
  - Each row is a **user**.
  - Each column is a **feature** that summarizes some aspect of that user's
    listening behavior or taste.

### main.py

- `main.py` is the **orchestrator**.
- Responsibilities:
  - Load raw listening history (and any required metadata).
  - Call into **specialized feature modules** (extractors) to compute specific
    feature groups.
  - Merge everything into a single user-level dataframe.
  - Write the final result to `features_df.csv`.

The goal is that `main.py` is the **only entrypoint most people need**. All
detailed feature logic should live in the submodules below.

### Extractor contract

All feature modules implement a shared extractor interface defined in
`_contract.py`:

- **Function signature**:
```python def extract(listening_history: pd.DataFrame) -> pd.DataFrame: ... ```
- **Input**:
  - Raw listening history with at least the columns listed in `EXPECTED_COLUMNS`
    in `_contract.py`
(e.g., `user_id`, `listen_timestamp`, `track_mbid`, `artist_mbid`, `album_mbid`,
`genre`, and core audio feature columns).
- **Output**:
  - A dataframe **keyed by `user_id`** (either indexed by `user_id` or with a
    `user_id` column).
  - Only the feature columns for that family (no label columns, no side
    effects).

`main.py` loads the listening history once, applies the global cutoff timestamp,
and then calls each registered extractor from `extractors/` (see below),
outer-joining their outputs on `user_id` and writing the merged result to
`features_df.csv`.

### Column naming convention

To avoid collisions when multiple modules add features, each module should
prefix its columns consistently:

- **basic** (`extractors/basic.py`): existing names like `total_tracks`,
  `n_unique_tracks`,
`avg_*`, `genre_*` (already established).
- **temporal** (`extractors/temporal.py`): `temporal_*` columns, e.g.
  `temporal_night_ratio`.
- **genre**: higher-level genre features such as `genre_entropy`,
  `genre_mainstream_score`, etc.
- **audio_features**: `audio_*` columns for learned or engineered audio
  embeddings.
- **album**: `album_*` columns summarizing album-level behavior.
- **artist**: `artist_*` columns summarizing artist affinity.

New modules should follow the same pattern to keep the feature space
interpretable.

### Feature module structure

Each module should:
- Focus on **one coherent family of features**.
- Expose a **clear, narrow interface** (e.g., a function that takes raw logs for
  a set
of users and returns a dataframe keyed by `user_id`).
- Avoid side effects beyond computing and returning features.

Current grouping (reflecting our team's taxonomy):

- `temporal.py`
  - Features capturing **when** and **how** users listen:
    - Time-of-day / day-of-week patterns.
    - Session dynamics, recency/novelty, streaks, etc.

- `genre.py` (or equivalent)
  - Features summarizing **genre preferences and diversity**:
    - Genre distributions, entropy, long-tail vs. mainstream tendencies.

- `audio_features.py`
  - Features derived from **track-level audio embeddings / descriptors**:
    - Averages and distributions of tempo, energy, valence, etc.
    - Any learned audio embeddings aggregated per user.

- `album.py`
  - Features around **album-level behavior**:
    - Album loyalty, completion rates, depth vs. breadth across albums.

- `artist.py`
  - Features summarizing **artist affinity**:
    - Top artists, concentration vs. exploration across artists.

New feature families should be added as **new, focused modules** rather than
expanding existing ones.

### Contract: features_df.csv

`features_df.csv` is the **canonical user-feature table** for downstream
training. At a minimum:
- Has one row per user.
- Includes a stable **user identifier column** (e.g., `user_id`).
- All other columns are numeric or well-defined categorical encodings.

Other parts of the training pipeline (e.g., label generation and model training)
should treat this file as the **single source of truth for user features**.
