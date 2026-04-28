"""Optional GCS download for ``past_listening_history.csv`` (large; not in git).

Configure in Streamlit Secrets (or local `.streamlit/secrets.toml`): a ``[gcs]`` table
with ``bucket``, ``object_name``, and ``credentials_json`` (full service-account JSON).
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import streamlit as st
from google.cloud import storage
from google.oauth2 import service_account

from dashboard.config import PathsConfig
from utils.logger import get_logger

_LOG = get_logger(__name__)

_STABLE_LOCAL_NAME = "past_listening_history_gcs.csv"


def _gcs_config_block() -> dict[str, str] | None:
    try:
        gcs = st.secrets["gcs"]
    except (FileNotFoundError, KeyError, TypeError):
        return None
    return dict(gcs)


def _parse_credentials_json(raw: str) -> dict:
    stripped = raw.strip()
    if stripped.startswith("{"):
        return json.loads(stripped)
    return json.loads(stripped)


@st.cache_data(show_spinner="Downloading listening history from GCS…", ttl=43_200)
def _download_listening_history_to_temp(
    bucket_name: str,
    object_name: str,
) -> str:
    block = _gcs_config_block()
    if block is None:
        raise RuntimeError("GCS secrets disappeared after cache was scheduled")

    credentials_json = block.get("credentials_json")
    if not credentials_json:
        raise KeyError(
            "secrets['gcs']['credentials_json'] is required for GCS listening history"
        )

    info = _parse_credentials_json(str(credentials_json))
    credentials = service_account.Credentials.from_service_account_info(info)
    project = info.get("project_id")
    client = storage.Client(credentials=credentials, project=project)

    dest_dir = Path(tempfile.gettempdir()) / "spotdate-listening-gcs"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / _STABLE_LOCAL_NAME

    bucket = client.bucket(bucket_name.strip())
    blob = bucket.blob(object_name.strip())
    _LOG.info(
        "Downloading gs://%s/%s → %s (size unknown until complete)",
        bucket_name,
        object_name,
        dest,
    )
    blob.download_to_filename(dest)
    _LOG.info("Finished GCS download → %s", dest)
    return str(dest.resolve())


def resolve_listening_history_csv_path(paths: PathsConfig) -> Path | None:
    """Resolve path for ``past_listening_history.csv``: GCS first, then bundle, then repo ``data/``."""
    gcs = _gcs_config_block()
    if (
        gcs
        and gcs.get("bucket")
        and gcs.get("object_name")
        and gcs.get("credentials_json")
    ):
        try:
            path_str = _download_listening_history_to_temp(
                str(gcs["bucket"]),
                str(gcs["object_name"]),
            )
            downloaded = Path(path_str)
            if downloaded.is_file():
                return downloaded
        except Exception:
            _LOG.exception(
                "GCS listening-history download failed; falling back to on-disk artifacts if present"
            )

    bundled = paths.artifact_root / "data" / "past_listening_history.csv"
    if bundled.is_file():
        return bundled

    legacy = paths.repo_root / "data" / "past_listening_history.csv"
    if legacy.is_file():
        return legacy

    return None
