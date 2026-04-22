from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity

from dashboard.config import CONFIG, DashboardConfig
from dashboard.models import compute_embeddings_for_model
from dashboard.services.aliases import build_alias_catalog
from dashboard.services.data import load_app_datasets, load_demo_datasets
from dashboard.services.scoring import build_user_group_scores, rank_pair_groups
from dashboard.types import AliasCatalog, ModelArtifactSpec, ModelBundle, PairContext


@st.cache_data(show_spinner=False)
def load_alias_catalog(demo_mode: bool = False) -> AliasCatalog:
    datasets = load_demo_datasets() if demo_mode else load_app_datasets()
    return build_alias_catalog(datasets.raw_features.reset_index(drop=True), CONFIG)


def _build_demo_model_spec(
    model_key: str, config: DashboardConfig = CONFIG
) -> ModelArtifactSpec:
    family_map = {family.key: family for family in config.model_families}
    family = family_map[model_key]
    return ModelArtifactSpec(
        key=model_key,
        label=f"{family.label} (Demo)",
        manifest_path=config.paths.dashboard_dir / "README.md",
        model_path=config.paths.dashboard_dir / "README.md",
        selection_metric="demo_score",
        selection_value=1.0,
        metadata={
            "avg_score": 0.84 if model_key == "autoencoder" else 0.88,
            "hit_rate_at_k": 0.8 if model_key == "autoencoder" else 0.86,
            "precision_at_high_score": 0.62 if model_key == "autoencoder" else 0.68,
            "recall_at_top_5_percent": 0.57 if model_key == "autoencoder" else 0.64,
            "mode": "demo",
        },
    )


def _compute_demo_embeddings_for_model(
    model_key: str,
    model_matrix: pd.DataFrame,
    config: DashboardConfig = CONFIG,
) -> tuple[ModelArtifactSpec, np.ndarray]:
    matrix = model_matrix.to_numpy(dtype=np.float32)
    if matrix.shape[1] == 0:
        raise ValueError("Demo model matrix is empty.")

    if model_key == "autoencoder":
        embedding_dim = min(8, matrix.shape[1])
        embeddings = matrix[:, :embedding_dim]
    elif model_key == "siamese":
        embedding_dim = min(6, matrix.shape[1])
        projection = np.linspace(
            0.25, 1.25, num=matrix.shape[1] * embedding_dim, dtype=np.float32
        ).reshape(matrix.shape[1], embedding_dim)
        embeddings = np.tanh(matrix @ projection)
    else:
        raise KeyError(f"Unsupported model family: {model_key}")

    return _build_demo_model_spec(model_key, config), np.asarray(embeddings)


@st.cache_resource(show_spinner=False)
def load_model_bundle(
    model_key: str,
    dataset_fingerprint: str,
    input_dim: int,
    demo_mode: bool = False,
) -> ModelBundle:
    del dataset_fingerprint, input_dim

    datasets = load_demo_datasets() if demo_mode else load_app_datasets()
    if demo_mode:
        spec, embeddings = _compute_demo_embeddings_for_model(
            model_key, datasets.model_matrix
        )
    else:
        spec, embeddings = compute_embeddings_for_model(model_key, datasets.model_matrix)

    similarity_matrix = cosine_similarity(embeddings)
    np.fill_diagonal(similarity_matrix, -np.inf)

    coordinates = PCA(n_components=2, random_state=42).fit_transform(embeddings)
    projection = pd.DataFrame(
        {
            "user_id": datasets.model_matrix.index,
            "x": coordinates[:, 0],
            "y": coordinates[:, 1],
        }
    )

    return ModelBundle(
        spec=spec,
        embeddings=embeddings,
        similarity_matrix=similarity_matrix,
        projection=projection,
    )


def get_model_bundle(model_key: str) -> ModelBundle:
    datasets = load_app_datasets()
    return load_model_bundle(
        model_key=model_key,
        dataset_fingerprint=datasets.fingerprint,
        input_dim=datasets.model_matrix.shape[1],
    )


def get_demo_model_bundle(model_key: str) -> ModelBundle:
    datasets = load_demo_datasets()
    return load_model_bundle(
        model_key=model_key,
        dataset_fingerprint=datasets.fingerprint,
        input_dim=datasets.model_matrix.shape[1],
        demo_mode=True,
    )


def build_pair_context(
    model_key: str,
    selected_user_id: str,
    config: DashboardConfig = CONFIG,
    demo_mode: bool = False,
) -> PairContext:
    datasets = load_demo_datasets() if demo_mode else load_app_datasets()
    alias_catalog = load_alias_catalog(demo_mode=demo_mode)
    model_bundle = (
        get_demo_model_bundle(model_key) if demo_mode else get_model_bundle(model_key)
    )
    group_scores = build_user_group_scores(datasets.raw_features, config)

    if selected_user_id not in datasets.model_matrix.index:
        raise KeyError(f"Unknown selected user: {selected_user_id}")

    selected_idx = datasets.model_matrix.index.get_loc(selected_user_id)
    ordered_indices = np.argsort(model_bundle.similarity_matrix[selected_idx])[::-1]

    recommendations = []
    for index in ordered_indices[: config.ui.top_match_count]:
        match_user_id = datasets.model_matrix.index[index]
        recommendations.append(
            {
                "user_id": match_user_id,
                "Alias": alias_catalog.alias_by_user_id[match_user_id],
                "Predicted Similarity": float(
                    model_bundle.similarity_matrix[selected_idx, index]
                ),
                "Future Alignment": datasets.future_alignment_lookup.get(
                    (selected_user_id, match_user_id)
                ),
                "Listener Profile": datasets.raw_features.loc[
                    match_user_id, "user_type_loyal"
                ],
            }
        )

    top_matches = pd.DataFrame(recommendations)
    best_match = top_matches.iloc[0]
    match_user_id = str(best_match["user_id"])
    future_alignment_score = datasets.future_alignment_lookup.get(
        (selected_user_id, match_user_id)
    )

    projection = model_bundle.projection.copy()
    projection["Alias"] = projection["user_id"].map(alias_catalog.alias_by_user_id)
    projection["Listener Profile"] = projection["user_id"].map(
        datasets.raw_features["user_type_loyal"].to_dict()
    )
    projection["role"] = "Cohort"
    projection.loc[projection["user_id"] == selected_user_id, "role"] = "Selected"
    projection.loc[projection["user_id"] == match_user_id, "role"] = "Match"

    group_rankings = rank_pair_groups(
        selected_user_id=selected_user_id,
        match_user_id=match_user_id,
        user_group_scores=group_scores,
        config=config,
    )

    demo_user = next(
        option
        for option in alias_catalog.demo_users
        if option.user_id == selected_user_id
    )

    return PairContext(
        model_key=model_key,
        model_label=model_bundle.spec.label,
        model_spec=model_bundle.spec,
        demo_user=demo_user,
        selected_user_id=selected_user_id,
        selected_alias=alias_catalog.alias_by_user_id[selected_user_id],
        selected_profile=datasets.raw_features.loc[selected_user_id],
        match_user_id=match_user_id,
        match_alias=alias_catalog.alias_by_user_id[match_user_id],
        match_profile=datasets.raw_features.loc[match_user_id],
        predicted_similarity=float(best_match["Predicted Similarity"]),
        future_alignment_score=future_alignment_score,
        top_matches=top_matches,
        projection=projection,
        group_rankings=group_rankings,
    )
