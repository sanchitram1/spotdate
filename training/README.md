## Training

This folder contains all code and notebooks related to **learning a neural model that
can suggest promising dating matches based on Spotify listening behavior**.

### Problem framing

We have:
- **Listening history**: user–track interactions over time.
- **Track-level metadata**: genres, audio features, artist/album info, etc.

We want to **build a dating product for users**, where good matches are users whose
musical journeys are compatible. The core challenge is that the data is **unlabeled**:
we do not directly know which pairs of users are "good matches".

Our current working thesis is:
- **Good matches ≈ users who share a similar listening trajectory over time** (what they
  listen to, how that evolves, and in what contexts).

To operationalize this, the training pipeline is split into two major steps:
1. **Labeling** – generate synthetic/heuristic labels that approximate "good match"
   pairs.
2. **Feature extraction** – compute user-level features that should help a model
   recognize those good matches.

Downstream, these labels and features will be used to train/validate ranking or
retrieval models that, given a user, surface candidate matches.

### Folder structure

- `labeling/`
  - **Goal**: turn raw listening histories into **pairwise labels** indicating which
    users look like good matches.
  - Main script: `label_generation.py`, which:
    - Splits interaction data into **past** and **future** windows.
    - Uses only the **future** window to define heuristic rules for when two users
      "match" (based on shared trajectories).
    - Outputs an **edgelist CSV** of candidate pairs with scores:
      - Columns: `anchor`, `positive`, `match_score`.
      - Each anchor has the **top-k (currently 7)** positives according to the heuristic
        score.
  - These labels are the **supervision signal** for training matching models.

- `feature_extraction/`
  - **Goal**: transform raw listening logs + track metadata into a **user-level feature
    matrix**.
  - Main script: `main.py`, which:
    - Takes listening history (and supporting metadata) as input.
    - Invokes a set of **targeted feature modules** (temporal, genre, audio features,
      album, artist).
    - Writes out `features_df.csv`, where:
      - Each row corresponds to a **user**.
      - Each column is a **feature** describing that user's listening behavior or taste.
  - These features are the **input space** for models trained on the labels from
    `labeling/`.

### High-level model structure

Conceptually, our matching system is built around:
- **Inputs**
  - User-level feature vectors from `feature_extraction` (e.g., temporal dynamics, genre
    and artist preferences, audio embedding summaries).
  - Pairwise labels from `labeling` indicating which user–user pairs are good matches.
- **Model objective**
  - Learn a representation space (e.g., via a neural encoder) where:
    - **Positive pairs** (heuristically good matches) are **close**.
    - Non-matching or random pairs are **far apart**.
  - This can be instantiated as contrastive learning, metric learning, or
    retrieval/ranking objectives.
- **Serving**
  - Given a user, encode them into the learned space and retrieve nearest neighbors as
    **candidate dating matches**.

This folder does **not** fix one specific neural architecture yet; instead, it defines
the **data contracts and abstractions** (labels and features) that any downstream model
must respect.

