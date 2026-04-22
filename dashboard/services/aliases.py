from __future__ import annotations

from itertools import product

from dashboard.config import CONFIG, DashboardConfig, DemoUserConfig
from dashboard.types import AliasCatalog, DemoUserOption

import pandas as pd


ADJECTIVES = (
    "Amber",
    "Aurora",
    "Beacon",
    "Bluebird",
    "Cinder",
    "Cobalt",
    "Comet",
    "Crimson",
    "Current",
    "Dawn",
    "Drift",
    "Echo",
    "Ember",
    "Evergreen",
    "Fable",
    "Flicker",
    "Golden",
    "Harbor",
    "Horizon",
    "Indigo",
    "Juniper",
    "Lattice",
    "Lucid",
    "Marble",
    "Meadow",
    "Metro",
    "Midnight",
    "Mirage",
    "Mosaic",
    "Nimbus",
    "Nova",
    "Orbit",
    "Pacific",
    "Parade",
    "Prism",
    "Quartz",
    "Radiant",
    "Rally",
    "Riot",
    "River",
    "Saffron",
    "Signal",
    "Solar",
    "Static",
    "Summit",
    "Tempo",
    "Velvet",
    "Verve",
    "Vivid",
    "Wild",
)

NOUNS = (
    "Arc",
    "Atlas",
    "Bloom",
    "Cadence",
    "Canvas",
    "Circuit",
    "Cloud",
    "Compass",
    "Crescent",
    "Current",
    "Drift",
    "Echo",
    "Ember",
    "Field",
    "Frame",
    "Garden",
    "Glint",
    "Groove",
    "Harbor",
    "Haze",
    "Horizon",
    "Index",
    "Junction",
    "Lagoon",
    "Lantern",
    "Loop",
    "Meadow",
    "Mirror",
    "Nova",
    "Orbit",
    "Parade",
    "Path",
    "Pulse",
    "Reverb",
    "Ribbon",
    "Ridge",
    "Signal",
    "Skyline",
    "Static",
    "Story",
    "Stripe",
    "Studio",
    "Summit",
    "Thread",
    "Trail",
    "Transit",
    "Valley",
    "Vector",
    "Vista",
    "Wave",
)


def _rank_demo_candidates(
    features: pd.DataFrame, demo_user: DemoUserConfig
) -> list[str]:
    if demo_user.selection_strategy == "max":
        column = demo_user.columns[0]
        ranked = features.sort_values(column, ascending=False)
        return ranked["user_id"].tolist()

    if demo_user.selection_strategy == "median_distance":
        distances = pd.Series(0.0, index=features.index)
        for column in demo_user.columns:
            distances = distances + (features[column] - features[column].median()).abs()

        ranked = features.loc[:, ["user_id"]].copy()
        ranked["_distance"] = distances
        ranked = ranked.sort_values("_distance", ascending=True)
        return ranked["user_id"].tolist()

    raise ValueError(
        f"Unsupported demo selection strategy: {demo_user.selection_strategy}"
    )


def select_demo_users(
    features: pd.DataFrame,
    config: DashboardConfig = CONFIG,
) -> tuple[DemoUserOption, ...]:
    used_user_ids: set[str] = set()
    options: list[DemoUserOption] = []

    for demo_user in config.demo_users:
        for user_id in _rank_demo_candidates(features, demo_user):
            if user_id in used_user_ids:
                continue
            used_user_ids.add(user_id)
            options.append(
                DemoUserOption(
                    key=demo_user.key,
                    alias=demo_user.alias,
                    user_id=user_id,
                    blurb=demo_user.blurb,
                )
            )
            break

    return tuple(options)


def build_alias_catalog(
    features: pd.DataFrame,
    config: DashboardConfig = CONFIG,
) -> AliasCatalog:
    demo_users = select_demo_users(features.reset_index(drop=True), config)
    alias_by_user_id = {option.user_id: option.alias for option in demo_users}
    user_id_by_alias = {option.alias: option.user_id for option in demo_users}

    used_aliases = set(user_id_by_alias)
    generated_aliases = (
        f"{adjective} {noun}" for adjective, noun in product(ADJECTIVES, NOUNS)
    )

    for user_id in sorted(features["user_id"].astype(str).tolist()):
        if user_id in alias_by_user_id:
            continue

        for alias in generated_aliases:
            if alias in used_aliases:
                continue
            alias_by_user_id[user_id] = alias
            user_id_by_alias[alias] = user_id
            used_aliases.add(alias)
            break

    return AliasCatalog(
        demo_users=demo_users,
        alias_by_user_id=alias_by_user_id,
        user_id_by_alias=user_id_by_alias,
    )
