from __future__ import annotations

from dashboard.ideas.flow import FlowIdea
from dashboard.ideas.radar import RadarIdea


def get_implementation_ideas() -> tuple[FlowIdea, RadarIdea]:
    return (FlowIdea(), RadarIdea())
