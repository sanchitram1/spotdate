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
import csv
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


def _detect_delimiter(path: Path) -> str:
    """Match ``dashboard.services.data.detect_delimiter`` without importing heavy deps.

    Must read only the first line: ``past_listening_history.csv`` can be multi-gigabyte.
    """
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        line = handle.readline()
    return ";" if line.count(";") > line.count(",") else ","


# Columns required by `dashboard.components.implementation_ideas` listening scans.
_LISTENING_TRIM_COLS = (
    "user_id",
    "track_name",
    "artist_name",
    "genre",
    "duration_ms",
)


def _write_trimmed_listening_history(
    repo_root: Path,
    dest_features_path: Path,
    dest_history_path: Path,
) -> None:
    """Subset of ``data/past_listening_history.csv`` for users present in bundled features only."""
    source = repo_root / "data" / "past_listening_history.csv"
    if not source.is_file():
        print(
            f"Skipping trimmed listening history: source not found ({source})",
            file=sys.stderr,
        )
        return

    feats_delim = _detect_delimiter(dest_features_path)
    allowed = set(
        pd.read_csv(
            dest_features_path,
            delimiter=feats_delim,
            usecols=["user_id"],
            dtype=str,
        )["user_id"]
        .astype(str)
        .tolist()
    )

    delim = _detect_delimiter(source)

    header = pd.read_csv(source, delimiter=delim, nrows=0)
    missing = [c for c in _LISTENING_TRIM_COLS if c not in header.columns]
    if missing:
        raise KeyError(
            f"{source} missing columns {missing}; cannot build dashboard listening subset"
        )

    dest_history_path.parent.mkdir(parents=True, exist_ok=True)
    rows_out = 0
    with source.open("r", encoding="utf-8", newline="") as raw_in:
        reader = csv.DictReader(raw_in, delimiter=delim)
        with dest_history_path.open("w", encoding="utf-8", newline="") as raw_out:
            writer = csv.DictWriter(
                raw_out,
                fieldnames=list(_LISTENING_TRIM_COLS),
                delimiter=delim,
                extrasaction="ignore",
            )
            writer.writeheader()
            for row in reader:
                uid_raw = row.get("user_id")
                if uid_raw is None:
                    continue
                if str(uid_raw).strip() not in allowed:
                    continue
                writer.writerow({c: row.get(c, "") for c in _LISTENING_TRIM_COLS})
                rows_out += 1

    if rows_out == 0:
        print(
            "Warning: trimmed listening history is empty "
            "(no rows for dashboard user ids in features_df)",
            file=sys.stderr,
        )
        return

    try:
        shown = dest_history_path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        shown = dest_history_path.resolve()
    print(
        f"Trimmed listening history ({rows_out} rows) → {shown}",
        file=sys.stderr,
    )


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

    feats_dest = dest_root / "data" / "features_df.csv"
    _write_trimmed_listening_history(
        repo_root,
        feats_dest,
        dest_root / "data" / "past_listening_history.csv",
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
