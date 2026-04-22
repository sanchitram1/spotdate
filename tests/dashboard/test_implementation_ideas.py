from __future__ import annotations

from dashboard.ideas.registry import get_implementation_ideas


def test_implementation_idea_registry_is_unique_and_complete() -> None:
    ideas = get_implementation_ideas()

    assert len(ideas) == 7
    assert [idea.key for idea in ideas] == [
        "flow",
        "new_radar",
        "match_dna",
        "opposites",
        "quirks",
        "flip_card",
        "stats",
    ]
    assert len({idea.key for idea in ideas}) == len(ideas)
