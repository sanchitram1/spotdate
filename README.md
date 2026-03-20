# spotdate

This is a repo for the Analytics Lab Project; IEOR 243 at UC Berkeley. In
general, the idea is to create a music dating application, matching people based
on shared listening histories / music consumption pattern.

## Setup

We use [uv](https://docs.astral.sh/uv/) from Astral for dependency management
and virtual environments.

### 1. Install uv

macOS / Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows (PowerShell):

```
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Create the venv

```bash
uv sync
```

### 3. Activate the venv

```bash
source .venv/bin/activate
```

## Committing and Merging

```bash
uv run ruff format /path/to/directory/or/file
uv run ruff check  /path/to/directory/or/file --fix
```

## Agent Context

This is a reusable context that you can drop into your chat to give them a basic understanding
of the project

```md
**Goal:**
- Build a recommendation system to predict high-quality user-to-user matches based on future listening trajectories
- Map users into higher dimensional "Taste Space" where Euclidean distance represents compatibility.

**Data Sources & Structure:**
- **Schema:** `ListeningHistory(User_ID, Listen_Timestamp, Track_ID, ...track_level_metadata)`, with user_id and listen_timestamp as the primary key
- **Temporal Split:** Strict temporal firewall. Data before Dec 31, 2013 is used for feature extraction (past_df); data after is used for ground truth labels (future_df).
- **Entities:** Users are represented by UUIDs.
- **final_features.csv:** User-level aggregated behavioral and metadata features (e.g., total tracks, avg acousticness, Artist Discovery Rate, Linear Listener Index). user_id is the index.
- **edgelist.csv (Ground Truth):** A flat list of verified future matches. Schema: [user_id_anchor, user_id_positive, similarity_score]

The final two csv files are available in the data directory. 

**Models in Scope:**
1. K-Means Clustering (Unsupervised baseline)
2. Autoencoder (Unsupervised embedding)
3. Siamese Network (Supervised, uses Triplet Margin Loss with dynamic negative sampling).

**Evaluation**
All models are judged based on five metrics:

| Metric | Goal | Description | How to calculate? | 
| ------ | ---- | ----------- | ----------------- |
| Hit Rate @ K | **Utility:** are users going to get jaded with our suggestions? | Does the model find any of the "True" matches in its Top-K suggestions? | For each user, if at least one of the model's Top-K suggestions is in the ground truth `top_k_edgelist`, it's a "Hit". Average this across all users. |
| Precision @ K | **Trust:** when our model says "Match", is it right? | Of the $K$ people the model suggested, how many are actually "High Score" matches? | $\frac{\text{Count of model suggestions in high score edgelist}}{K}$ – averaged across all users |
| Recall @ Top 5 | **Coverage:** Is our model finding needles in the haystack? | How many of the "Gold Standard" matches did the model find? | $\frac{\text{Count of model suggestions that appear in the top 5 pct}}{\text{Total number of items in the top 5 pct}}$ |
| Mean Rank | **Discovery:** Are the best matches consistently at the top of the list? | On average, how far down is the true match in the model's output? (Lower is better) | For every "True" match, find its rank in the model's sorted list (1st, 10th, 500th). Average these ranks. |
| Omission Count | **Anti-discovery:** How many good matches did we fail to discover? | The raw count of true Top-K matches that the model failed to identify | $K - (\text{Count of model suggestions found in top k edgelist})$.|
```