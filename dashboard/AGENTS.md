# Dashboard AGENTS.md

## Mission

The `dashboard/` package exists to turn the Spotdate training artifacts into a
clear, product-facing demo.

This is **not** the training pipeline itself. The dashboard's job is to:

1. load saved user features, edgelists, and trained model artifacts
2. compute match recommendations from those saved artifacts
3. explain those recommendations in a way that is easy for humans to inspect
4. prototype implementation ideas such as `Flow` and `Radar`

When working in this area, optimize for:

- clarity over cleverness
- modular sections over one-off inline code
- deterministic demo behavior
- product explanation grounded in real saved artifacts

## Core Task

The dashboard should answer:

- "What does the model think is a good match for this user?"
- "How do we explain that match in a product?"
- "What visual/storytelling pattern would make the match understandable?"

The current dashboard answers those questions with:

- a model selector for `Autoencoder` vs `Siamese Network`
- a small alias-based demo user selector
- a top-level embedding + recommendation view
- two implementation ideas:
  - `Flow`: Wrapped-style story cards
  - `Radar`: dynamic pair-specific taste axes

## Repo Navigation

Use this path map when orienting yourself:

- `dashboard/app.py`
  - Streamlit entrypoint
  - wires the sidebar controls and renders the page sections

- `dashboard/config.py`
  - the single source of truth for dashboard configuration
  - holds artifact paths, model-family metadata, demo aliases, semantic groups,
    UI copy, and style tokens
  - start here before changing behavior or content

- `dashboard/components/`
  - presentation-only page sections
  - these should render existing state, not re-load data or models

- `dashboard/ideas/`
  - one module per implementation idea
  - new ideas should follow the `build(...)` + `render(...)` pattern and be
    registered in `dashboard/ideas/registry.py`

- `dashboard/services/`
  - data loading, alias selection, pair-context building, semantic scoring
  - this is the main orchestration layer for "how the dashboard thinks"

- `dashboard/models/`
  - logic for discovering the best saved artifact from manifests and loading it
  - this layer should hide TensorFlow / Torch specifics from the UI

- `dashboard/types.py`
  - shared typed containers used across services and components

- `tests/dashboard/`
  - targeted tests for preprocessing, alias selection, model loading, scoring,
    and end-to-end pair-context assembly

- `data/`
  - copied runtime data used by the dashboard
  - treat these as input artifacts, not normal source files

- `training/models/experiments/`
  - copied saved model artifacts and manifests
  - the dashboard reads from these directories but should not rewrite them

- `training/models/*.ipynb`
  - source-of-truth reference for how the models were trained and what their
    saved artifacts mean
  - use these notebooks to confirm preprocessing or model architecture details

## How To Work In This Area

### Safe defaults

- Prefer changing `dashboard/config.py` instead of scattering hardcoded values.
- Prefer adding new derived logic in `dashboard/services/` instead of
  components.
- Prefer using saved manifests to discover "best model" rather than naming
  specific files.
- Prefer deterministic demo user selection and deterministic section ordering.

### What not to do

- Do not retrain models from the dashboard layer.
- Do not hardcode artifact filenames if they can be resolved from manifests.
- Do not make page components fetch data independently.
- Do not put complex scoring logic directly in Streamlit components.
- Do not edit the copied large CSV/model artifact files unless the task is
  explicitly about regenerating artifacts.

## Typical Change Routes

If the task is about a new section or implementation idea:

1. update `dashboard/config.py` if you need new copy or semantic groups
2. add or update logic in `dashboard/services/scoring.py` or
   `dashboard/services/contexts.py`
3. create a new module in `dashboard/ideas/`
4. register it in `dashboard/ideas/registry.py`
5. add focused tests in `tests/dashboard/`

If the task is about model loading:

1. read `dashboard/agent_guides/model_retrieval.md`
2. inspect `dashboard/models/`
3. confirm behavior against `training/models/*.ipynb`

If the task is about charts or visual direction:

1. read `dashboard/agent_guides/visualization_style_guide.md`
2. inspect `dashboard/components/` and `dashboard/ideas/`
3. keep presentation changes separate from scoring / loading logic

If the task is about feature columns or edgelists:

1. read `dashboard/agent_guides/data_shapes.md`
2. inspect `dashboard/services/data.py`
3. confirm any assumptions against files in `data/`

## Read These Guides

- `dashboard/agent_guides/visualization_style_guide.md`
- `dashboard/agent_guides/model_retrieval.md`
- `dashboard/agent_guides/data_shapes.md`

## Useful Commands

Run the app:

```bash
uv run streamlit run dashboard/app.py
```

Run dashboard tests:

```bash
uv run pytest tests/dashboard -q
```

Format / lint dashboard code:

```bash
uv run ruff format dashboard tests/dashboard
uv run ruff check dashboard tests/dashboard --fix
```

## Agent Heuristics

- Start with `config.py`, then `services/`, then `components/` or `ideas/`.
- If a behavior feels "pair-specific", it probably belongs in
  `dashboard/services/contexts.py` or `dashboard/services/scoring.py`.
- If a behavior feels "display-specific", it probably belongs in
  `dashboard/components/` or `dashboard/ideas/`.
- If a change affects both models, make sure the abstraction still works for
  both TensorFlow and Torch-backed artifacts.
- Always preserve the dashboard's main promise: explain real model outputs using
  understandable, product-ready storytelling.
