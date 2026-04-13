# Dashboard

This package contains the Streamlit match dashboard for the Spotdate model demo.

## Run locally

```bash
uv run streamlit run dashboard/app.py
```

The app reads:

- `data/features_df.csv`
- `data/edgelists/edgelist_full.csv`
- saved model manifests and artifacts under `training/models/experiments`

## What it shows

- a model selector for the saved autoencoder and siamese model families
- a curated 5-user alias selector
- a top-level embedding visualization and recommendation table
- two implementation ideas:
  - `Flow`: Wrapped-style story cards
  - `Radar`: dynamic, pair-specific taste axes

## Add a new section or implementation idea

1. Add any new copy, thresholds, or semantic signals to [config.py](/Users/sanch/workspace/spotify-app-dashboard/dashboard/config.py).
2. Create a new module in `dashboard/ideas/` that implements `build(context, config)` and `render(payload, context, config)`.
3. Register the idea in [registry.py](/Users/sanch/workspace/spotify-app-dashboard/dashboard/ideas/registry.py).
4. If the section needs new pair-scoring inputs, extend `dashboard/services/scoring.py` using config-defined semantic groups instead of hardcoding one-off logic.
5. Add focused tests in `tests/dashboard/` for the new payload builder and any new scoring behavior.
