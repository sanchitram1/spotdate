from __future__ import annotations

from typing import Any, Protocol

from dashboard.config import DashboardConfig
from dashboard.types import PairContext


class ImplementationIdea(Protocol):
    key: str
    title: str
    kind: str
    description: str

    def build(self, context: PairContext, config: DashboardConfig) -> Any: ...

    def render(
        self, payload: Any, context: PairContext, config: DashboardConfig
    ) -> None: ...
