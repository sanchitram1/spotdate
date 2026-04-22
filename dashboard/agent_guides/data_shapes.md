# Data Shapes Guide

## Purpose

This guide explains the runtime data the dashboard depends on and what shape the
dashboard expects after preprocessing.

The dashboard is not inventing demo data. It reads copied artifacts from `data/`
and uses them directly.

## Main Runtime Inputs

### 1. `data/features_df.csv`

This is the main user-feature table.

Expected properties:

- one row per user
- includes a `user_id` column
- includes numeric features and some categorical/bool columns
- used as the base matrix for both models

Examples of feature families visible in the saved file:

- temporal features
  - `temporal_night_ratio`
  - `temporal_peak_hour`
  - `temporal_*`

- genre features
  - `genre_unique_count`
  - `genre_entropy`
  - `genre_evenness`

- aggregate audio features
  - `avg_energy`
  - `avg_valence`
  - `avg_tempo`
  - `variance_*`

- behavioral / loyalty features
  - `loyal_track_count`
  - `early_loyal_ratio`
  - `favorite_genre_ratio`

- exploration / mainstreamness features
  - `nunique_artist`
  - `artist_concentration_index`
  - `one_hit_wonder`
  - `hipster_gap`

- categorical / bool features
  - `user_type_loyal`
  - `emotional_state`
  - `explicit_mode`

### 2. `data/edgelists/edgelist_full.csv`

This is the future-alignment lookup used to annotate the predicted match.

Expected columns:

- `user_anchor`
- `user_match`
- `similarity_score`

The dashboard does **not** use this file to choose the top predicted match.
Instead:

- the model embeddings choose the match
- the edgelist provides the future-alignment reference score for that pair

### 3. Saved Model Artifacts

These live in:

- `training/models/experiments/`

Important files:

- many saved model files
- `manifest.csv` files with evaluation metrics and paths

## Dashboard Preprocessing Shape

The dashboard mirrors the notebook preprocessing:

1. read `features_df.csv`
2. preserve `user_id`
3. drop `user_id` from the model input matrix
4. one-hot encode object/string/bool columns
5. fill missing values using medians, then zeros for any leftovers
6. standardize with `StandardScaler`

Result:

- index: `user_id`
- columns: transformed feature columns suitable for the saved models
- values: standardized numeric matrix

This logic lives in:

- `dashboard/services/data.py`

## Higher-Level Derived Shapes

### Alias catalog

Built in:

- `dashboard/services/aliases.py`

Shape:

- 5 deterministic demo users with fixed aliases
- auto-generated aliases for the rest of the cohort

### User semantic-group scores

Built in:

- `dashboard/services/scoring.py`

Shape:

- index: `user_id`
- columns: semantic groups like `energy`, `mood`, `tempo`, `loyalty`
- values: percentile-normalized scores in `[0, 1]`

### Pair context

Built in:

- `dashboard/services/contexts.py`

This is the central runtime object for the UI.
It contains:

- selected model metadata
- selected demo user
- top predicted match
- top-k recommendations
- future alignment score
- embedding projection points
- ranked semantic-group explanations

## Important Rules

- `features_df.csv` is the primary source of user-level dashboard state.
- `edgelist_full.csv` is a reference layer, not the dashboard's recommendation
  engine.
- semantic groups should be defined in `dashboard/config.py`, not inferred
  ad hoc in UI code.
- if you add a new feature-dependent explanation, confirm the source columns
  exist in `features_df.csv` first.

## When To Read Training Docs

Open training docs or notebooks when:

- you are unsure whether a column is raw vs engineered
- you need to confirm why a model expects a certain input shape
- you need to map saved manifest metadata back to notebook logic

The most relevant training references are:

- `training/feature_extraction/README.md`
- `training/labeling/README.md`
- `training/models/autoencoder.ipynb`
- `training/models/siamese.ipynb`
