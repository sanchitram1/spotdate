from __future__ import annotations

from typing import Any

import pandas as pd

from dashboard.config import CONFIG, DashboardConfig
from dashboard.types import ModelArtifactSpec


def _normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    normalized = {}
    for key, value in record.items():
        if hasattr(value, "item"):
            normalized[key] = value.item()
        else:
            normalized[key] = value
    return normalized


def select_best_model_spec(
    model_key: str,
    file_suffix: str,
    config: DashboardConfig = CONFIG,
) -> ModelArtifactSpec:
    family_map = {family.key: family for family in config.model_families}
    if model_key not in family_map:
        raise KeyError(f"Unsupported model family: {model_key}")

    candidates: list[ModelArtifactSpec] = []

    for manifest_path in sorted(config.paths.experiments_dir.rglob("manifest.csv")):
        manifest = pd.read_csv(manifest_path)
        if "model_path" not in manifest.columns:
            continue

        for record in manifest.to_dict("records"):
            record = _normalize_record(record)
            model_path = config.paths.training_models_dir / str(record["model_path"])

            if model_path.suffix != file_suffix or not model_path.exists():
                continue

            if config.model_selection.metric not in record:
                continue

            candidates.append(
                ModelArtifactSpec(
                    key=model_key,
                    label=family_map[model_key].label,
                    manifest_path=manifest_path,
                    model_path=model_path,
                    selection_metric=config.model_selection.metric,
                    selection_value=float(record[config.model_selection.metric]),
                    metadata=record,
                )
            )

    if not candidates:
        raise FileNotFoundError(f"No {model_key} artifacts found with suffix {file_suffix}")

    return max(candidates, key=lambda spec: spec.selection_value)

