from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dashboard.config import CONFIG
from dashboard.services.aliases import build_alias_catalog
from dashboard.services.data import load_app_datasets_uncached


@pytest.fixture(scope="session")
def datasets():
    return load_app_datasets_uncached(CONFIG)


@pytest.fixture(scope="session")
def alias_catalog(datasets):
    return build_alias_catalog(datasets.raw_features.reset_index(drop=True), CONFIG)
