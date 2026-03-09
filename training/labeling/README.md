## Labeling

This module is responsible for **creating training labels that approximate "good
matches" between users**, starting from raw listening history. Since we do not observe
ground-truth dating outcomes, our labels are **heuristic** and based on how users'
listening trajectories align.

### Problem: no explicit match labels

We want to recommend **dating matches** between users, but:
- We only observe **listening behavior** and metadata.
- We **do not** observe direct feedback like "these two users went on a date and liked
  each other".

To bootstrap supervised learning, we treat **shared listening trajectories** as a proxy:
- Users whose future listening behavior is **highly aligned** (under some rules) are
  treated as **positive pairs**.
- All other pairs are treated as non-matches or ignored.

### label_generation.py

`label_generation.py` implements the current heuristic pipeline:

- **1. Temporal split**
  - Split the data into **past** and **future** windows.
  - The **future window** is used only for **label construction**, to approximate how
    user tastes co-evolve.

- **2. Heuristic match rules**
  - Within the future window, define rules that quantify how "aligned" two users are,
    for example:
    - Overlap in what they listen to.
    - Similar evolution or shifts in taste over time.
  - These rules combine into a **match_score** that ranks how good a match two users
    appear to be.

- **3. Edgelist output**
  - For each **anchor user**, select their **top-k (currently 7)** candidate matches by
    `match_score`.
  - Emit an **edgelist CSV** with columns:
    - `anchor` – the user for whom we are finding matches.
    - `positive` – a user that appears to be a good match for the anchor.
    - `match_score` – the heuristic score for that pair.

This edgelist is the **supervision signal** used to train models that learn a user
representation or directly score user–user pairs.

### Downstream usage

The edgelist produced here is intended to be:
- Joined with user-level features from `feature_extraction/features_df.csv`.
- Used to train contrastive / metric-learning / ranking models where:
  - Edges `(anchor, positive)` are treated as **positive examples**.
  - Random or hard-negative pairs are treated as **negative examples**.

As we iterate on the product and gather real feedback, this heuristic labeling can be:
- Refined (better trajectory definitions, new similarity metrics).
- Complemented or replaced with **observed user feedback** where available.
- Based on a separate NNs definition of track similarity, to define similar listening
  trajectories

