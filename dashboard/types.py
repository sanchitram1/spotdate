from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ModelArtifactSpec:
    key: str
    label: str
    manifest_path: Path
    model_path: Path
    selection_metric: str
    selection_value: float
    metadata: dict[str, Any]


@dataclass
class LoadedDatasets:
    raw_features: pd.DataFrame
    model_matrix: pd.DataFrame
    full_edgelist: pd.DataFrame
    future_alignment_lookup: dict[tuple[str, str], float]
    fingerprint: str


@dataclass(frozen=True)
class DemoUserOption:
    key: str
    alias: str
    user_id: str
    blurb: str


@dataclass
class AliasCatalog:
    demo_users: tuple[DemoUserOption, ...]
    alias_by_user_id: dict[str, str]
    user_id_by_alias: dict[str, str]


@dataclass
class ModelBundle:
    spec: ModelArtifactSpec
    embeddings: np.ndarray
    similarity_matrix: np.ndarray
    projection: pd.DataFrame


@dataclass
class PairContext:
    model_key: str
    model_label: str
    model_spec: ModelArtifactSpec
    demo_user: DemoUserOption
    selected_user_id: str
    selected_alias: str
    selected_profile: pd.Series
    match_user_id: str
    match_alias: str
    match_profile: pd.Series
    predicted_similarity: float
    future_alignment_score: float | None
    top_matches: pd.DataFrame
    projection: pd.DataFrame
    group_rankings: pd.DataFrame
