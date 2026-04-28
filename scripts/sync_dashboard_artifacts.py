#!/usr/bin/env uv run python
"""Populate ``dashboard/artifacts/`` with the smallest runnable Streamlit subset.

Reads the same best ``.keras`` / ``.pt`` picks as ``select_best_model_spec`` against the
training tree (not ``dashboard/artifacts`` yet), then copies CSVs plus two trimmed
``manifest.csv`` rows that point into the bundle.

Run from repo root:
    uv run python scripts/sync_dashboard_artifacts.py
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dashboard.config import build_config  # noqa: E402
from dashboard.models.common import select_best_model_spec  # noqa: E402
from dashboard.types import ModelArtifactSpec  # noqa: E402


def _trimmed_manifest_row(
    spec: ModelArtifactSpec, new_relative_model_path: str
) -> pd.DataFrame:
    manifest = pd.read_csv(spec.manifest_path)
    subset = manifest[
        manifest["model_path"].astype(str) == str(spec.metadata["model_path"])
    ]
    if subset.empty:
        raise ValueError(
            f"No manifest row matching {spec.metadata['model_path']!r} in {spec.manifest_path}"
        )
    row = subset.iloc[[0]].copy()
    row.loc[:, "model_path"] = new_relative_model_path
    return row


def sync_dashboard_artifacts(repo_root: Path, *, extra_listening_history: bool) -> None:
    discovery = build_config(repo_root, prefer_dashboard_bundle=False)
    dest_root = repo_root / "dashboard" / "artifacts"
    ae = select_best_model_spec("autoencoder", ".keras", discovery)
    si = select_best_model_spec("siamese", ".pt", discovery)

    (dest_root / "data").mkdir(parents=True, exist_ok=True)
    (dest_root / "data" / "edgelists").mkdir(parents=True, exist_ok=True)
    (dest_root / "training" / "models" / "experiments").mkdir(
        parents=True, exist_ok=True
    )

    shutil.copy2(discovery.paths.features_path, dest_root / "data" / "features_df.csv")
    shutil.copy2(
        discovery.paths.full_edgelist_path,
        dest_root / "data" / "edgelists" / discovery.paths.full_edgelist_path.name,
    )

    if extra_listening_history:
        lp = repo_root / "data" / "past_listening_history.csv"
        if lp.is_file():
            shutil.copy2(lp, dest_root / "data" / "past_listening_history.csv")
        else:
            print(f"Skipping past_listening_history: not found ({lp})", file=sys.stderr)

    ae_dir_rel = Path("experiments") / "autoencoder_dashboard"
    si_dir_rel = Path("experiments") / "siamese_dashboard"
    ae_name = "dashboard_best.keras"
    si_name = "dashboard_best.pt"
    ae_out_dir = dest_root / "training" / "models" / ae_dir_rel
    si_out_dir = dest_root / "training" / "models" / si_dir_rel
    ae_out_dir.mkdir(parents=True, exist_ok=True)
    si_out_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(ae.model_path, ae_out_dir / ae_name)
    shutil.copy2(si.model_path, si_out_dir / si_name)

    ae_manifest_rel = f"{ae_dir_rel.as_posix()}/{ae_name}"
    si_manifest_rel = f"{si_dir_rel.as_posix()}/{si_name}"

    _trimmed_manifest_row(ae, ae_manifest_rel).to_csv(
        ae_out_dir / "manifest.csv", index=False
    )
    _trimmed_manifest_row(si, si_manifest_rel).to_csv(
        si_out_dir / "manifest.csv", index=False
    )

    refreshed = build_config(repo_root)
    print(f"Synced bundle under {dest_root.relative_to(repo_root)!s}", file=sys.stderr)
    print(
        f"Reloaded CONFIG artifact_root → {refreshed.paths.artifact_root}",
        file=sys.stderr,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy minimal dashboard runtime bundle."
    )
    parser.add_argument(
        "--with-listening-history",
        action="store_true",
        help="Also copy data/past_listening_history.csv if present (very large).",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=REPO_ROOT,
        help="Repository root",
    )
    return parser.parse_args()


def main() -> None:
    ns = parse_args()
    sync_dashboard_artifacts(
        ns.repo.resolve(), extra_listening_history=ns.with_listening_history
    )


if __name__ == "__main__":
    main()
