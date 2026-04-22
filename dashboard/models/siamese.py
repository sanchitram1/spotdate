from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st
import torch
import torch.nn as nn

from dashboard.config import CONFIG, DashboardConfig
from dashboard.models.common import select_best_model_spec
from dashboard.types import ModelArtifactSpec


DEPTH_TO_LAYERS = {
    2: [128, 64],
    3: [256, 128, 64],
}


class UserEmbeddingMLP(nn.Module):
    def __init__(
        self,
        input_dim: int,
        embedding_dim: int,
        layers: list[int],
        dropout_rate: float,
    ) -> None:
        super().__init__()

        modules: list[nn.Module] = []
        previous_dim = input_dim

        for layer_size in layers:
            modules.append(nn.Linear(previous_dim, layer_size))
            modules.append(nn.ReLU())
            modules.append(nn.Dropout(dropout_rate))
            previous_dim = layer_size

        modules.append(nn.Linear(previous_dim, embedding_dim))
        self.network = nn.Sequential(*modules)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        return self.network(inputs)


def resolve_layers(depth: int) -> list[int]:
    if depth not in DEPTH_TO_LAYERS:
        raise ValueError(f"Unsupported siamese depth: {depth}")
    return DEPTH_TO_LAYERS[depth]


def get_siamese_spec(config: DashboardConfig = CONFIG) -> ModelArtifactSpec:
    return select_best_model_spec("siamese", ".pt", config)


@st.cache_resource(show_spinner=False)
def load_siamese_model(
    model_path: str,
    input_dim: int,
    embedding_dim: int,
    depth: int,
    dropout_rate: float,
) -> UserEmbeddingMLP:
    model = UserEmbeddingMLP(
        input_dim=input_dim,
        embedding_dim=embedding_dim,
        layers=resolve_layers(depth),
        dropout_rate=dropout_rate,
    )
    state_dict = torch.load(model_path, map_location="cpu")
    model.load_state_dict(state_dict)
    model.eval()
    return model


def compute_siamese_embeddings(
    model_matrix: pd.DataFrame,
    config: DashboardConfig = CONFIG,
) -> tuple[ModelArtifactSpec, np.ndarray]:
    spec = get_siamese_spec(config)
    metadata = spec.metadata

    model = load_siamese_model(
        model_path=str(spec.model_path),
        input_dim=model_matrix.shape[1],
        embedding_dim=int(metadata["embedding_dim"]),
        depth=int(metadata["depth"]),
        dropout_rate=float(metadata["dropout_rate"]),
    )

    inputs = torch.tensor(model_matrix.to_numpy(dtype=np.float32), dtype=torch.float32)
    with torch.no_grad():
        embeddings = model(inputs).cpu().numpy()

    return spec, embeddings
