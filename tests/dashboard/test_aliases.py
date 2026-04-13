from __future__ import annotations

from dashboard.config import CONFIG
from dashboard.services.aliases import select_demo_users


def test_demo_user_selection_is_unique(datasets) -> None:
    demo_users = select_demo_users(datasets.raw_features.reset_index(drop=True), CONFIG)

    assert len(demo_users) == 5
    assert len({option.user_id for option in demo_users}) == 5
    assert [option.alias for option in demo_users] == [
        option.alias for option in CONFIG.demo_users
    ]


def test_demo_user_selection_uses_expected_extrema(datasets) -> None:
    features = datasets.raw_features.reset_index(drop=True)
    selected = {
        option.key: option.user_id for option in select_demo_users(features, CONFIG)
    }

    assert (
        selected["night_owl"]
        == features.sort_values("temporal_night_ratio", ascending=False).iloc[0][
            "user_id"
        ]
    )
    assert (
        selected["high_energy"]
        == features.sort_values("avg_energy", ascending=False).iloc[0]["user_id"]
    )
    assert (
        selected["high_diversity"]
        == features.sort_values("genre_unique_count", ascending=False).iloc[0][
            "user_id"
        ]
    )
    assert (
        selected["high_hipster"]
        == features.sort_values("hipster_gap", ascending=False).iloc[0]["user_id"]
    )

    median_distance = (
        (features["avg_energy"] - features["avg_energy"].median()).abs()
        + (features["genre_entropy"] - features["genre_entropy"].median()).abs()
        + (features["avg_tempo"] - features["avg_tempo"].median()).abs()
    )
    used_before_median = {
        selected["night_owl"],
        selected["high_energy"],
        selected["high_diversity"],
        selected["high_hipster"],
    }
    ranking = features.loc[:, ["user_id"]].copy()
    ranking["_distance"] = median_distance
    median_candidate = (
        ranking.loc[lambda frame: ~frame["user_id"].isin(used_before_median)]
        .sort_values("_distance", ascending=True)
        .iloc[0]["user_id"]
    )
    assert selected["median_profile"] == median_candidate
