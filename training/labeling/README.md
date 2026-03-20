## Labeling

This module is responsible for **creating training labels that approximate "good
matches" between users**, starting from raw listening history. Since we do not
observe ground-truth dating outcomes, our labels are **heuristic** and based on
how users' listening trajectories align.

### Problem: no explicit match labels

We want to recommend **dating matches** between users, but:
- We only observe **listening behavior** and metadata.
- We **do not** observe direct feedback like "these two users went on a date and
liked each other".

To bootstrap supervised learning, we treat **shared listening trajectories** as
a proxy:
- Users whose future listening behavior is **highly aligned** (under some rules)
are treated as **positive pairs**.
- All other pairs are treated as non-matches or ignored.

### heuristics.py

`heuristics.py` implements the current heuristic pipeline:

- **1. Temporal split**
  - Split the data into **past** and **future** windows.
  - The **future window** is used only for **label construction**, to
approximate how user tastes co-evolve.

- **2. Heuristic match rules**
  - Within the future window, define rules that quantify how "aligned" two users
are, for example:
    - Overlap in what they listen to.
    - Similar evolution or shifts in taste over time.
  - These rules combine into a **match_score** that ranks how good a match two
users appear to be.

- **3. Edgelist output**
  - For each **anchor user**, select their **top-k (currently 7)** candidate
matches by `match_score`.
  - Emit an **edgelist CSV** with columns:
    - `anchor` – the user for whom we are finding matches.
    - `positive` – a user that appears to be a good match for the anchor.
    - `match_score` – the heuristic score for that pair.

This edgelist is the **supervision signal** used to train models that learn a
user representation or directly score user–user pairs.

#### Downstream usage

The edgelist produced here is intended to be:
- Joined with user-level features from `feature_extraction/features_df.csv`.
- Used to train contrastive / metric-learning / ranking models where:
  - Edges `(anchor, positive)` are treated as **positive examples**.
  - Random or hard-negative pairs are treated as **negative examples**.

As we iterate on the product and gather real feedback, this heuristic labeling
can be:
- Refined (better trajectory definitions, new similarity metrics).
- Complemented or replaced with **observed user feedback** where available.
- Based on a separate NNs definition of track similarity, to define similar
listening trajectories

### clustering.py

`clustering.py` implements a cluster-based labeling pipeline that represents
each user as a **probability distribution over music taste clusters**, then
uses cosine similarity between those distributions to find good matches.

- **1. Fit KMeans on track features**
  - Train a KMeans model (default 12 clusters) on audio feature columns
    (`danceability`, `energy`, `tempo`, `valence`, `acousticness`,
    `instrumentalness`, `liveness`, `speechiness`, `loudness`) from a tracks
    dataset.
  - Features are standardized via `StandardScaler` before clustering.

- **2. Predict clusters on listening history**
  - Rather than joining listening history back to tracks on `track_mbid`, we
    use the fitted scaler + KMeans to **predict** a cluster label directly on
    each listening history row (which must carry the same audio feature
    columns).

- **3. Build per-user cluster distribution vectors**
  - For each user, count how many of their listened tracks fall into each
    cluster, then **normalize to a probability distribution** (row sums to
    1.0).
  - This means a user is **not** reduced to a single "favorite cluster".
    Instead, they are represented as a vector like
    `[0.30, 0.00, 0.15, ..., 0.55]` capturing the full shape of their
    listening taste across all clusters.

- **4. Cosine similarity on distribution vectors**
  - Compute pairwise cosine similarity between all user distribution vectors.
  - **This is the key insight**: we are not comparing users by their single
    top cluster. We are comparing the **full shape** of each user's listening
    profile. Two users who split their listening across clusters in a similar
    way will score highly, even if neither has a single dominant cluster.

- **5. Three edgelist outputs**
  - All outputs share the same columns: `user_anchor`, `user_match`,
    `similarity_score`.
  - **`edgelist_topK`** – For every user, their top-K most similar matches
    (default K=10). Every user in the input is guaranteed to appear as a
    `user_anchor`.
  - **`edgelist_full`** – Every ordered `(i, j)` pair where `i ≠ j`, with
    scores. Every user appears as a `user_anchor`.
  - **`edgelist_high_scores`** – Only pairs whose similarity exceeds a
    cutoff threshold (default 0.85). Users with no matches above the cutoff
    will not appear.

A guard in `main` validates that no users were lost between the input
listening history and the final edgelists (users can be dropped if all of
their feature rows are NaN).

