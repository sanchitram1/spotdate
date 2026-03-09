## Feature extraction

This module is responsible for **turning raw listening history + track metadata into a
clean, user-level feature table** that downstream models can train on.

At a high level:
- **Input**: user–track interaction logs (listening history) and track-level metadata
  (genres, audio features, album and artist info).
- **Output**: `features_df.csv`, where:
  - Each row is a **user**.
  - Each column is a **feature** that summarizes some aspect of that user's listening
    behavior or taste.

### main.py

- `main.py` is the **orchestrator**.
- Responsibilities:
  - Load raw listening history (and any required metadata).
  - Call into **specialized feature modules** to compute specific feature groups.
  - Merge everything into a single dataframe.
  - Write the final result to `features_df.csv`.

The goal is that `main.py` is the **only entrypoint most people need**. All detailed
feature logic should live in the submodules below.

### Feature module structure

Each module should:
- Focus on **one coherent family of features**.
- Expose a **clear, narrow interface** (e.g., a function that takes raw logs for a set
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

New feature families should be added as **new, focused modules** rather than expanding
existing ones.

### Contract: features_df.csv

`features_df.csv` is the **canonical user-feature table** for downstream training. At a
minimum:
- Has one row per user.
- Includes a stable **user identifier column** (e.g., `user_id`).
- All other columns are numeric or well-defined categorical encodings.

Other parts of the training pipeline (e.g., label generation and model training) should
treat this file as the **single source of truth for user features**.
