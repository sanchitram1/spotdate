from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
import streamlit as st
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler

from dashboard.config import CONFIG, DashboardConfig
from dashboard.types import ArtifactStatus, LoadedDatasets


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


def inspect_artifact_status(config: DashboardConfig = CONFIG) -> ArtifactStatus:
    features_available = config.paths.features_path.exists()
    full_edgelist_available = config.paths.full_edgelist_path.exists()

    available_model_keys: list[str] = []
    experiments_available = False

    for family in config.model_families:
        has_model = False
        for manifest_path in sorted(config.paths.experiments_dir.rglob("manifest.csv")):
            manifest = pd.read_csv(manifest_path)
            if "model_path" not in manifest.columns:
                continue

            for model_path_value in manifest["model_path"].astype(str):
                model_path = config.paths.training_models_dir / model_path_value
                if model_path.suffix == family.file_suffix and model_path.exists():
                    has_model = True
                    break

            if has_model:
                break

        if has_model:
            available_model_keys.append(family.key)

    experiments_available = len(available_model_keys) == len(config.model_families)

    missing_paths: list[str] = []
    if not features_available:
        missing_paths.append(str(config.paths.features_path))
    if not full_edgelist_available:
        missing_paths.append(str(config.paths.full_edgelist_path))
    if not config.paths.experiments_dir.exists():
        missing_paths.append(str(config.paths.experiments_dir))
    elif not experiments_available:
        missing_paths.append(str(config.paths.experiments_dir / "**" / "manifest.csv"))

    return ArtifactStatus(
        features_available=features_available,
        full_edgelist_available=full_edgelist_available,
        experiments_available=experiments_available,
        available_model_keys=tuple(available_model_keys),
        missing_paths=tuple(missing_paths),
    )


def _build_demo_features() -> pd.DataFrame:
    rows = [
        {
            "user_id": "demo_001",
            "temporal_night_ratio": 0.92,
            "avg_energy": 0.76,
            "genre_unique_count": 28,
            "hipster_gap": 0.66,
            "genre_entropy": 0.82,
            "avg_tempo": 132.0,
            "pct_high_energy": 0.74,
            "pct_low_energy": 0.08,
            "avg_valence": 0.62,
            "pct_happy_tracks": 0.58,
            "pct_sad_tracks": 0.16,
            "pct_fast_tracks": 0.68,
            "pct_slow_tracks": 0.09,
            "night_energy_mean": 0.79,
            "night_valence_mean": 0.57,
            "genre_evenness": 0.79,
            "nunique_artist": 115,
            "artist_concentration_index": 0.19,
            "one_hit_wonder": 0.23,
            "pct_underground_tracks": 0.63,
            "pct_viral_tracks": 0.11,
            "loyal_track_count": 38,
            "early_loyal_ratio": 0.41,
            "favorite_genre_ratio": 0.29,
            "user_type_loyal": "Explorer",
            "emotional_state": "Bright",
            "explicit_mode": True,
        },
        {
            "user_id": "demo_002",
            "temporal_night_ratio": 0.35,
            "avg_energy": 0.95,
            "genre_unique_count": 15,
            "hipster_gap": 0.18,
            "genre_entropy": 0.49,
            "avg_tempo": 148.0,
            "pct_high_energy": 0.91,
            "pct_low_energy": 0.03,
            "avg_valence": 0.72,
            "pct_happy_tracks": 0.69,
            "pct_sad_tracks": 0.08,
            "pct_fast_tracks": 0.89,
            "pct_slow_tracks": 0.04,
            "night_energy_mean": 0.71,
            "night_valence_mean": 0.62,
            "genre_evenness": 0.52,
            "nunique_artist": 74,
            "artist_concentration_index": 0.44,
            "one_hit_wonder": 0.11,
            "pct_underground_tracks": 0.19,
            "pct_viral_tracks": 0.42,
            "loyal_track_count": 44,
            "early_loyal_ratio": 0.47,
            "favorite_genre_ratio": 0.51,
            "user_type_loyal": "Power Listener",
            "emotional_state": "Bright",
            "explicit_mode": False,
        },
        {
            "user_id": "demo_003",
            "temporal_night_ratio": 0.44,
            "avg_energy": 0.58,
            "genre_unique_count": 36,
            "hipster_gap": 0.38,
            "genre_entropy": 0.91,
            "avg_tempo": 118.0,
            "pct_high_energy": 0.46,
            "pct_low_energy": 0.19,
            "avg_valence": 0.55,
            "pct_happy_tracks": 0.47,
            "pct_sad_tracks": 0.21,
            "pct_fast_tracks": 0.41,
            "pct_slow_tracks": 0.18,
            "night_energy_mean": 0.54,
            "night_valence_mean": 0.48,
            "genre_evenness": 0.88,
            "nunique_artist": 146,
            "artist_concentration_index": 0.15,
            "one_hit_wonder": 0.35,
            "pct_underground_tracks": 0.37,
            "pct_viral_tracks": 0.14,
            "loyal_track_count": 19,
            "early_loyal_ratio": 0.21,
            "favorite_genre_ratio": 0.22,
            "user_type_loyal": "Explorer",
            "emotional_state": "Reflective",
            "explicit_mode": False,
        },
        {
            "user_id": "demo_004",
            "temporal_night_ratio": 0.61,
            "avg_energy": 0.49,
            "genre_unique_count": 24,
            "hipster_gap": 0.94,
            "genre_entropy": 0.71,
            "avg_tempo": 108.0,
            "pct_high_energy": 0.32,
            "pct_low_energy": 0.28,
            "avg_valence": 0.43,
            "pct_happy_tracks": 0.28,
            "pct_sad_tracks": 0.34,
            "pct_fast_tracks": 0.24,
            "pct_slow_tracks": 0.31,
            "night_energy_mean": 0.47,
            "night_valence_mean": 0.39,
            "genre_evenness": 0.68,
            "nunique_artist": 109,
            "artist_concentration_index": 0.22,
            "one_hit_wonder": 0.44,
            "pct_underground_tracks": 0.81,
            "pct_viral_tracks": 0.03,
            "loyal_track_count": 27,
            "early_loyal_ratio": 0.34,
            "favorite_genre_ratio": 0.26,
            "user_type_loyal": "Crate Digger",
            "emotional_state": "Moody",
            "explicit_mode": True,
        },
        {
            "user_id": "demo_005",
            "temporal_night_ratio": 0.48,
            "avg_energy": 0.63,
            "genre_unique_count": 22,
            "hipster_gap": 0.41,
            "genre_entropy": 0.66,
            "avg_tempo": 121.0,
            "pct_high_energy": 0.53,
            "pct_low_energy": 0.12,
            "avg_valence": 0.51,
            "pct_happy_tracks": 0.44,
            "pct_sad_tracks": 0.18,
            "pct_fast_tracks": 0.49,
            "pct_slow_tracks": 0.14,
            "night_energy_mean": 0.59,
            "night_valence_mean": 0.49,
            "genre_evenness": 0.63,
            "nunique_artist": 96,
            "artist_concentration_index": 0.28,
            "one_hit_wonder": 0.27,
            "pct_underground_tracks": 0.34,
            "pct_viral_tracks": 0.18,
            "loyal_track_count": 31,
            "early_loyal_ratio": 0.37,
            "favorite_genre_ratio": 0.33,
            "user_type_loyal": "Follower/Others",
            "emotional_state": "Balanced",
            "explicit_mode": False,
        },
        {
            "user_id": "demo_006",
            "temporal_night_ratio": 0.18,
            "avg_energy": 0.37,
            "genre_unique_count": 12,
            "hipster_gap": 0.12,
            "genre_entropy": 0.34,
            "avg_tempo": 92.0,
            "pct_high_energy": 0.11,
            "pct_low_energy": 0.54,
            "avg_valence": 0.31,
            "pct_happy_tracks": 0.19,
            "pct_sad_tracks": 0.43,
            "pct_fast_tracks": 0.08,
            "pct_slow_tracks": 0.57,
            "night_energy_mean": 0.28,
            "night_valence_mean": 0.27,
            "genre_evenness": 0.42,
            "nunique_artist": 48,
            "artist_concentration_index": 0.58,
            "one_hit_wonder": 0.06,
            "pct_underground_tracks": 0.15,
            "pct_viral_tracks": 0.37,
            "loyal_track_count": 52,
            "early_loyal_ratio": 0.59,
            "favorite_genre_ratio": 0.67,
            "user_type_loyal": "Loyalist",
            "emotional_state": "Melancholic",
            "explicit_mode": False,
        },
        {
            "user_id": "demo_007",
            "temporal_night_ratio": 0.71,
            "avg_energy": 0.68,
            "genre_unique_count": 31,
            "hipster_gap": 0.72,
            "genre_entropy": 0.78,
            "avg_tempo": 126.0,
            "pct_high_energy": 0.61,
            "pct_low_energy": 0.10,
            "avg_valence": 0.47,
            "pct_happy_tracks": 0.36,
            "pct_sad_tracks": 0.27,
            "pct_fast_tracks": 0.56,
            "pct_slow_tracks": 0.13,
            "night_energy_mean": 0.73,
            "night_valence_mean": 0.43,
            "genre_evenness": 0.73,
            "nunique_artist": 131,
            "artist_concentration_index": 0.18,
            "one_hit_wonder": 0.31,
            "pct_underground_tracks": 0.58,
            "pct_viral_tracks": 0.07,
            "loyal_track_count": 24,
            "early_loyal_ratio": 0.28,
            "favorite_genre_ratio": 0.24,
            "user_type_loyal": "Night Owl",
            "emotional_state": "Moody",
            "explicit_mode": True,
        },
        {
            "user_id": "demo_008",
            "temporal_night_ratio": 0.29,
            "avg_energy": 0.57,
            "genre_unique_count": 18,
            "hipster_gap": 0.29,
            "genre_entropy": 0.58,
            "avg_tempo": 116.0,
            "pct_high_energy": 0.43,
            "pct_low_energy": 0.17,
            "avg_valence": 0.64,
            "pct_happy_tracks": 0.57,
            "pct_sad_tracks": 0.11,
            "pct_fast_tracks": 0.37,
            "pct_slow_tracks": 0.16,
            "night_energy_mean": 0.52,
            "night_valence_mean": 0.58,
            "genre_evenness": 0.55,
            "nunique_artist": 83,
            "artist_concentration_index": 0.34,
            "one_hit_wonder": 0.18,
            "pct_underground_tracks": 0.28,
            "pct_viral_tracks": 0.22,
            "loyal_track_count": 34,
            "early_loyal_ratio": 0.43,
            "favorite_genre_ratio": 0.38,
            "user_type_loyal": "Balanced",
            "emotional_state": "Bright",
            "explicit_mode": True,
        },
    ]
    return pd.DataFrame(rows)


def _build_demo_edgelist(raw_features: pd.DataFrame) -> pd.DataFrame:
    model_matrix = preprocess_features(raw_features)
    similarity_matrix = cosine_similarity(model_matrix)

    rows: list[dict[str, object]] = []
    user_ids = model_matrix.index.tolist()
    for anchor_index, user_anchor in enumerate(user_ids):
        for match_index, user_match in enumerate(user_ids):
            if anchor_index == match_index:
                continue
            similarity = float((similarity_matrix[anchor_index, match_index] + 1.0) / 2.0)
            rows.append(
                {
                    "user_anchor": user_anchor,
                    "user_match": user_match,
                    "similarity_score": round(similarity, 4),
                }
            )

    return pd.DataFrame(rows)


def load_demo_datasets_uncached(config: DashboardConfig = CONFIG) -> LoadedDatasets:
    del config

    raw_features = _build_demo_features()
    raw_features = raw_features.assign(user_id=raw_features["user_id"].astype(str))
    raw_features = raw_features.set_index("user_id", drop=False)

    full_edgelist = _build_demo_edgelist(raw_features.reset_index(drop=True))
    model_matrix = preprocess_features(raw_features.reset_index(drop=True))
    future_alignment_lookup = full_edgelist.set_index(["user_anchor", "user_match"])[
        "similarity_score"
    ].to_dict()

    return LoadedDatasets(
        raw_features=raw_features,
        model_matrix=model_matrix,
        full_edgelist=full_edgelist,
        future_alignment_lookup=future_alignment_lookup,
        fingerprint="demo-datasets-v1",
    )


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


@st.cache_data(show_spinner=False)
def load_demo_datasets() -> LoadedDatasets:
    return load_demo_datasets_uncached(CONFIG)
