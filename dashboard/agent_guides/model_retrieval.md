# Model Retrieval Guide

## Purpose

This guide explains how the dashboard finds and loads saved model artifacts.

The dashboard supports two model families:

- `Autoencoder` backed by TensorFlow `.keras` files
- `Siamese Network` backed by PyTorch `.pt` files

The app should always load saved artifacts from manifests, not hardcoded
filenames.

## Where The Artifacts Live

- manifests and saved models:
  - `training/models/experiments/`

- notebook references that explain what those files mean:
  - `training/models/autoencoder.ipynb`
  - `training/models/siamese.ipynb`

## Relevant Dashboard Files

- `dashboard/models/common.py`
  - scans manifest files
  - selects the best artifact for a requested model family

- `dashboard/models/autoencoder.py`
  - loads a `.keras` model
  - exposes the `bottleneck_output` layer as the embedding model

- `dashboard/models/siamese.py`
  - reconstructs the `UserEmbeddingMLP`
  - loads a `.pt` state dict
  - returns embedding outputs directly from the network forward pass

- `dashboard/models/__init__.py`
  - simple public facade for model discovery and embedding generation

## Selection Logic

The dashboard selects the best artifact using:

- the manifest rows under `training/models/experiments/**/manifest.csv`
- the metric named in `dashboard/config.py`
  - currently `avg_score`

For each row:

1. resolve `model_path`
2. check the file suffix matches the requested model family
3. check the model file actually exists
4. score candidates by the configured metric
5. pick the max

## Autoencoder Details

### Artifact type

- file suffix: `.keras`

### Loading steps

1. load the full TensorFlow model from disk
2. create a new TensorFlow model whose output is the named layer
   `bottleneck_output`
3. run the dashboard's preprocessed user matrix through that encoder

### Why this matters

The dashboard does not use the reconstruction output. It uses the latent
embedding because that is the user representation compared with cosine
similarity.

## Siamese Details

### Artifact type

- file suffix: `.pt`

### Loading steps

1. read the best manifest row
2. rebuild the `UserEmbeddingMLP` architecture from metadata
3. map notebook depth settings to layer stacks
4. load the PyTorch state dict
5. run the preprocessed user matrix through the network

### Current depth mapping

- `depth = 2` maps to `[128, 64]`
- `depth = 3` maps to `[256, 128, 64]`

These mappings come from the training notebook and should stay synchronized with
the saved artifact semantics.

## Important Constraints

- Never assume the best model filename by string matching alone.
- Never bypass manifest-based discovery if a manifest exists.
- Keep TensorFlow and Torch logic isolated inside `dashboard/models/`.
- If a notebook training definition changes, the dashboard loader may also need
  to change.

## If You Need To Debug A Loading Problem

1. confirm the model file exists in `training/models/experiments/`
2. inspect the matching `manifest.csv`
3. compare loader assumptions against the notebook definition
4. verify preprocessing shape matches what the model expects

## If You Add Another Model Family

1. add metadata to `dashboard/config.py`
2. add a dedicated loader module under `dashboard/models/`
3. extend `dashboard/models/common.py` or `dashboard/models/__init__.py`
4. add tests for:
   - manifest selection
   - model loading
   - embedding shape
   - end-to-end pair-context assembly
