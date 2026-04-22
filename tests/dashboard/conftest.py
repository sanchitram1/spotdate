from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dashboard.config import CONFIG  # noqa: E402
from dashboard.services.aliases import build_alias_catalog  # noqa: E402
from dashboard.services.data import (  # noqa: E402
    inspect_artifact_status,
    load_app_datasets_uncached,
)


@pytest.fixture(scope="session")
def datasets():
    if not inspect_artifact_status(CONFIG).ready:
        pytest.skip("Saved dashboard artifacts are not available in this workspace.")
    return load_app_datasets_uncached(CONFIG)


@pytest.fixture(scope="session")
def alias_catalog(datasets):
    return build_alias_catalog(datasets.raw_features.reset_index(drop=True), CONFIG)
