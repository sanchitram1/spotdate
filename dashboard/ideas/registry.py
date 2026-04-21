from __future__ import annotations

from dashboard.ideas.flow import FlowIdea
from dashboard.ideas.new_radar import NewRadarIdea
from dashboard.ideas.match_dna import MatchDNAIdea
from dashboard.ideas.opposites import OppositesIdea
from dashboard.ideas.quirks import QuirksIdea
from dashboard.ideas.flip_card import FlipCardIdea


def get_implementation_ideas() -> tuple[FlowIdea, NewRadarIdea, MatchDNAIdea, OppositesIdea, QuirksIdea, FlipCardIdea]:
    return (
        FlowIdea(), 
        NewRadarIdea(), 
        MatchDNAIdea(), 
        OppositesIdea(), 
        QuirksIdea(),
        FlipCardIdea()
    )
