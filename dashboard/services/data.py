from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
import streamlit as st
from sklearn.preprocessing import StandardScaler

from dashboard.config import CONFIG, DashboardConfig
from dashboard.types import LoadedDatasets


def detect_delimiter(path: Path) -> str:
    """Choose between the repo's semicolon convention and the saved CSV artifact."""
    header = path.read_text(encoding="utf-8").splitlines()[0]
    return ";" if header.count(";") > header.count(",") else ","


def read_delimited_csv(path: Path, dtype: dict[str, str] | None = None) -> pd.DataFrame:
    return pd.read_csv(path, delimiter=detect_delimiter(path), dtype=dtype)


def preprocess_features(raw_features: pd.DataFrame) -> pd.DataFrame:
    user_ids = raw_features["user_id"].astype(str)

    feature_frame = raw_features.drop(columns=["user_id"]).copy()
    categorical_columns = feature_frame.select_dtypes(
        include=["object", "string", "bool"]
    ).columns.tolist()
    encoded = pd.get_dummies(feature_frame, columns=categorical_columns)
    encoded = encoded.fillna(encoded.median(numeric_only=True))
    encoded = encoded.fillna(0.0)

    scaler = StandardScaler()
    scaled = scaler.fit_transform(encoded)

    return pd.DataFrame(
        scaled,
        index=user_ids,
        columns=encoded.columns,
    )


def _fingerprint(paths: PathsConfigLike) -> str:
    digest = hashlib.sha256()
    for path in (paths.features_path, paths.full_edgelist_path):
        stat = path.stat()
        digest.update(str(path).encode("utf-8"))
        digest.update(str(stat.st_size).encode("utf-8"))
        digest.update(str(stat.st_mtime_ns).encode("utf-8"))
    return digest.hexdigest()


class PathsConfigLike:
    features_path: Path
    full_edgelist_path: Path


def load_app_datasets_uncached(config: DashboardConfig = CONFIG) -> LoadedDatasets:
    raw_features = read_delimited_csv(
        config.paths.features_path, dtype={"user_id": str}
    )
    raw_features = raw_features.assign(user_id=raw_features["user_id"].astype(str))
    raw_features = raw_features.set_index("user_id", drop=False)

    full_edgelist = read_delimited_csv(
        config.paths.full_edgelist_path,
        dtype={"user_anchor": str, "user_match": str},
    )

    required_columns = {"user_anchor", "user_match", "similarity_score"}
    if not required_columns.issubset(full_edgelist.columns):
        missing = required_columns.difference(full_edgelist.columns)
        raise KeyError(f"Missing required edgelist columns: {sorted(missing)}")

    model_matrix = preprocess_features(raw_features.reset_index(drop=True))
    future_alignment_lookup = full_edgelist.set_index(["user_anchor", "user_match"])[
        "similarity_score"
    ].to_dict()

    return LoadedDatasets(
        raw_features=raw_features,
        model_matrix=model_matrix,
        full_edgelist=full_edgelist,
        future_alignment_lookup=future_alignment_lookup,
        fingerprint=_fingerprint(config.paths),
    )


@st.cache_data(show_spinner=False)
def load_app_datasets() -> LoadedDatasets:
    return load_app_datasets_uncached(CONFIG)
