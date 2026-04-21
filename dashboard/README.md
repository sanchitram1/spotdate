# Dashboard

This package contains the Streamlit match dashboard for the Spotdate model demo.

## Run locally

```bash
uv run streamlit run dashboard/app.py
```

If `uv` hits a local cache permission problem on Windows, run the app with the
repo venv directly instead:

```bash
.venv\Scripts\python.exe -m streamlit run dashboard\app.py
```

The app reads:

- `data/features_df.csv`
- `data/edgelists/edgelist_full.csv`
- saved model manifests and artifacts under `training/models/experiments`

## Startup behavior

The dashboard now supports two runtime modes:

- **Artifact mode**: used automatically when the saved CSVs and model artifacts
  are present
- **Built-in demo mode**: used automatically when those artifacts are missing,
  and also available as a toggle when artifact mode is available

Demo mode is deterministic and exists to unblock UI/product work while the
training outputs are unavailable.

## To activate the full dashboard with real artifacts

Restore or regenerate:

- `data/features_df.csv`
- `data/edgelists/edgelist_full.csv`
- `training/models/experiments/**/manifest.csv`
- the model files referenced by those manifests

## What it shows

- a model selector for the saved autoencoder and siamese model families
- a curated 5-user alias selector
- a runtime health panel explaining which data and artifacts are active
- a model comparison view for the same selected user across model families
- a top-level embedding visualization and recommendation table
- several implementation ideas, including:
  - `Flow`: Wrapped-style story cards
  - `Radar`: dynamic pair-specific taste axes
  - `Match DNA`, `Opposites`, `Quirks`, and `Flip Card` concepts

## Add a new section or implementation idea

1. Add any new copy, thresholds, or semantic signals to [config.py](/Users/sanch/workspace/spotify-app-dashboard/dashboard/config.py).
2. Create a new module in `dashboard/ideas/` that implements `build(context, config)` and `render(payload, context, config)`.
3. Register the idea in [registry.py](/Users/sanch/workspace/spotify-app-dashboard/dashboard/ideas/registry.py).
4. If the section needs new pair-scoring inputs, extend `dashboard/services/scoring.py` using config-defined semantic groups instead of hardcoding one-off logic.
5. Add focused tests in `tests/dashboard/` for the new payload builder and any new scoring behavior.
