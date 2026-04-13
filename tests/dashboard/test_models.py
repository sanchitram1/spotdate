from __future__ import annotations

from dashboard.models.autoencoder import (
    compute_autoencoder_embeddings,
    get_autoencoder_spec,
)
from dashboard.models.siamese import compute_siamese_embeddings, get_siamese_spec


def test_autoencoder_manifest_selection_returns_existing_artifact() -> None:
    spec = get_autoencoder_spec()

    assert spec.key == "autoencoder"
    assert spec.model_path.exists()
    assert spec.manifest_path.exists()
    assert "encoding_dim" in spec.metadata


def test_siamese_manifest_selection_returns_existing_artifact() -> None:
    spec = get_siamese_spec()

    assert spec.key == "siamese"
    assert spec.model_path.exists()
    assert spec.manifest_path.exists()
    assert "embedding_dim" in spec.metadata


def test_autoencoder_embedding_shape_matches_manifest(datasets) -> None:
    sample_matrix = datasets.model_matrix.head(8)
    spec, embeddings = compute_autoencoder_embeddings(sample_matrix)

    assert embeddings.shape == (8, int(spec.metadata["encoding_dim"]))


def test_siamese_embedding_shape_matches_manifest(datasets) -> None:
    sample_matrix = datasets.model_matrix.head(8)
    spec, embeddings = compute_siamese_embeddings(sample_matrix)

    assert embeddings.shape == (8, int(spec.metadata["embedding_dim"]))
