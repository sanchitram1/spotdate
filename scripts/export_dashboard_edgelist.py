#!/usr/bin/env uv run python
"""Stream `edgelist_full.csv`, keep edges whose anchor is one of the dashboard demo users.

Reads the same personas as ``select_demo_users`` (Sean, Daniel, …) from ``features_df.csv``
and writes ``data/edgelists/edgelist_dashboard_users.csv``. The dashboard resolves
``PathsConfig.full_edgelist_path`` to this file when it exists—deploy only this slice for
cheap future-alignment scans.

Examples:
    uv run python scripts/export_dashboard_edgelist.py
    uv run python scripts/export_dashboard_edgelist.py \\
        --features data/features_df.csv --source data/edgelists/edgelist_full.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dashboard.config import CONFIG, DashboardConfig, build_config  # noqa: E402
from dashboard.services.aliases import select_demo_users  # noqa: E402
from dashboard.services.data import detect_delimiter, read_delimited_csv  # noqa: E402

_DEFAULT_OUT = Path("data/edgelists/edgelist_dashboard_users.csv")
_CHUNK = 250_000


def parse_args() -> argparse.Namespace:
    artifact_root = CONFIG.paths.artifact_root
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument(
        "--artifact-root",
        type=Path,
        default=artifact_root,
        help="Repo artifact root containing data/ (default from CONFIG.paths.artifact_root)",
    )
    p.add_argument(
        "--features",
        type=Path,
        default=None,
        help="Override path to features_df.csv",
    )
    p.add_argument(
        "--source",
        type=Path,
        default=None,
        help="Override path to source edgelist (default artifact_root/edgelists/edgelist_full.csv)",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=_DEFAULT_OUT,
        help=f"Destination path (default: {_DEFAULT_OUT})",
    )
    return p.parse_args()


def export_dashboard_slice(
    *,
    features_path: Path,
    source_path: Path,
    destination: Path,
    config: DashboardConfig,
) -> int:
    if not features_path.is_file():
        raise FileNotFoundError(f"features not found: {features_path}")
    if not source_path.is_file():
        raise FileNotFoundError(f"source edgelist not found: {source_path}")

    features = read_delimited_csv(features_path, dtype={"user_id": str})
    demo_selection = select_demo_users(features.reset_index(drop=True), config)
    anchor_ids = frozenset(str(u.user_id) for u in demo_selection)

    delim = detect_delimiter(source_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    rows_written = 0
    header_written = False

    for chunk in pd.read_csv(
        source_path,
        delimiter=delim,
        dtype={"user_anchor": str, "user_match": str},
        chunksize=_CHUNK,
        low_memory=False,
    ):
        required = {"user_anchor", "user_match", "similarity_score"}
        if not required.issubset(chunk.columns):
            missing = sorted(required.difference(chunk.columns))
            raise KeyError(f"Missing edgelist columns: {missing}")

        hit = chunk[chunk["user_anchor"].astype(str).isin(anchor_ids)]
        if hit.empty:
            continue
        hit.to_csv(
            destination,
            mode="a",
            sep=delim,
            header=not header_written,
            index=False,
        )
        header_written = True
        rows_written += len(hit)

    aliases = ", ".join(f"{u.alias}={u.user_id}" for u in demo_selection)
    print(
        f"Wrote {rows_written:,} rows to {destination}",
        file=sys.stderr,
    )
    print(f"Anchors ({len(demo_selection)} personas): {aliases}", file=sys.stderr)
    return rows_written


def main() -> None:
    ns = parse_args()
    artifact_root = ns.artifact_root.resolve()
    cfg = build_config(artifact_root)
    features_path = (ns.features or (artifact_root / "data/features_df.csv")).resolve()
    source_path = (
        ns.source or (artifact_root / "data/edgelists/edgelist_full.csv")
    ).resolve()
    out_path = Path(ns.out).resolve()
    export_dashboard_slice(
        features_path=features_path,
        source_path=source_path,
        destination=out_path,
        config=cfg,
    )


if __name__ == "__main__":
    main()
