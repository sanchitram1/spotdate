from __future__ import annotations

import numpy as np
import pandas as pd

from dashboard.config import CONFIG
from dashboard.types import ModelArtifactSpec


def list_model_families() -> tuple[tuple[str, str], ...]:
    return tuple((family.key, family.label) for family in CONFIG.model_families)


def get_model_spec(model_key: str) -> ModelArtifactSpec:
    if model_key == "autoencoder":
        from dashboard.models.autoencoder import get_autoencoder_spec

        return get_autoencoder_spec(CONFIG)
    if model_key == "siamese":
        from dashboard.models.siamese import get_siamese_spec

        return get_siamese_spec(CONFIG)
    raise KeyError(f"Unsupported model family: {model_key}")


def compute_embeddings_for_model(
    model_key: str,
    model_matrix: pd.DataFrame,
) -> tuple[ModelArtifactSpec, np.ndarray]:
    if model_key == "autoencoder":
        from dashboard.models.autoencoder import compute_autoencoder_embeddings

        return compute_autoencoder_embeddings(model_matrix, CONFIG)
    if model_key == "siamese":
        from dashboard.models.siamese import compute_siamese_embeddings

        return compute_siamese_embeddings(model_matrix, CONFIG)
    raise KeyError(f"Unsupported model family: {model_key}")
