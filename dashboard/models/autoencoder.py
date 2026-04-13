from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st
import tensorflow as tf

from dashboard.config import CONFIG, DashboardConfig
from dashboard.models.common import select_best_model_spec
from dashboard.types import ModelArtifactSpec


def get_autoencoder_spec(config: DashboardConfig = CONFIG) -> ModelArtifactSpec:
    return select_best_model_spec("autoencoder", ".keras", config)


@st.cache_resource(show_spinner=False)
def load_autoencoder_encoder(model_path: str) -> tf.keras.Model:
    model = tf.keras.models.load_model(model_path, compile=False)
    encoder = tf.keras.Model(
        inputs=model.input,
        outputs=model.get_layer("bottleneck_output").output,
    )
    return encoder


def compute_autoencoder_embeddings(
    model_matrix: pd.DataFrame,
    config: DashboardConfig = CONFIG,
) -> tuple[ModelArtifactSpec, np.ndarray]:
    spec = get_autoencoder_spec(config)
    encoder = load_autoencoder_encoder(str(spec.model_path))
    embeddings = encoder.predict(model_matrix.to_numpy(dtype=np.float32), verbose=0)
    return spec, np.asarray(embeddings)
