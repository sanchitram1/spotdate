from __future__ import annotations

import pytest

from dashboard.config import CONFIG
from dashboard.ideas.flow import FlowIdea
from dashboard.ideas.radar import RadarIdea
from dashboard.services.contexts import build_pair_context


@pytest.mark.parametrize("model_key", ["autoencoder", "siamese"])
def test_pair_context_builds_flow_and_radar_payloads(
    alias_catalog, model_key: str
) -> None:
    selected_demo = alias_catalog.demo_users[0]
    context = build_pair_context(
        model_key=model_key, selected_user_id=selected_demo.user_id
    )

    assert context.selected_alias == selected_demo.alias
    assert not context.top_matches.empty
    assert context.match_alias

    flow_payload = FlowIdea().build(context, CONFIG)
    radar_payload = RadarIdea().build(context, CONFIG)

    assert len(flow_payload) == CONFIG.ui.flow_card_count
    assert len(radar_payload.axes) == CONFIG.ui.radar_axis_count
