from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PathsConfig:
    repo_root: Path
    artifact_root: Path
    dashboard_dir: Path
    features_path: Path
    full_edgelist_path: Path
    experiments_dir: Path
    training_models_dir: Path


@dataclass(frozen=True)
class ModelSelectionConfig:
    metric: str


@dataclass(frozen=True)
class ModelFamilyConfig:
    key: str
    label: str
    file_suffix: str
    summary: str


@dataclass(frozen=True)
class DemoUserConfig:
    key: str
    alias: str
    blurb: str
    selection_strategy: str
    columns: tuple[str, ...]


@dataclass(frozen=True)
class SemanticSignalConfig:
    column: str
    weight: float = 1.0
    invert: bool = False


@dataclass(frozen=True)
class SemanticGroupConfig:
    key: str
    label: str
    description: str
    story_lead: str
    signals: tuple[SemanticSignalConfig, ...]


@dataclass(frozen=True)
class UIConfig:
    app_title: str
    app_subtitle: str
    hero_intro_heading: str
    hero_intro_body: str
    app_description: str
    implementation_section_title: str
    top_match_count: int
    flow_card_count: int
    radar_axis_count: int


@dataclass(frozen=True)
class StyleConfig:
    background: str
    panel_background: str
    text_primary: str
    text_muted: str
    accent: str
    accent_secondary: str
    accent_tertiary: str


@dataclass(frozen=True)
class DashboardConfig:
    paths: PathsConfig
    model_selection: ModelSelectionConfig
    model_families: tuple[ModelFamilyConfig, ...]
    demo_users: tuple[DemoUserConfig, ...]
    semantic_groups: tuple[SemanticGroupConfig, ...]
    ui: UIConfig
    style: StyleConfig

    def model_labels(self) -> dict[str, str]:
        return {family.key: family.label for family in self.model_families}


def resolve_repo_root(
    *,
    config_file: Path | None = None,
    cwd: Path | None = None,
) -> Path:
    """Find the git checkout when ``dashboard`` is installed into site-packages.

    On Streamlit Community Cloud the process cwd is the repo root, but
    ``Path(__file__)`` may point under ``site-packages``, which would make
    ``parents[1]`` *not* the repo and break ``dashboard/artifacts/`` resolution.
    """
    explicit = os.environ.get("SPOTDATE_REPO_ROOT")
    if explicit:
        return Path(explicit).expanduser().resolve()

    anchor = (config_file or Path(__file__)).resolve()
    work = (cwd or Path.cwd()).resolve()
    derived_from_file = anchor.parents[1]

    candidates: list[Path] = []
    for p in (work, derived_from_file):
        if p not in candidates:
            candidates.append(p)

    bundle = Path("dashboard") / "artifacts" / "data" / "features_df.csv"
    app_entry = Path("dashboard") / "app.py"

    for base in candidates:
        if (base / bundle).is_file():
            return base
    for base in candidates:
        if (base / app_entry).is_file():
            return base

    return derived_from_file


def build_config(
    repo_root: Path | None = None,
    *,
    prefer_dashboard_bundle: bool = True,
) -> DashboardConfig:
    resolved_root = repo_root or resolve_repo_root()
    fallback_artifact_root = resolved_root.parent / "spotify-app"
    dashboard_bundle = resolved_root / "dashboard" / "artifacts"

    artifact_root = resolved_root
    if (
        prefer_dashboard_bundle
        and (dashboard_bundle / "data" / "features_df.csv").is_file()
    ):
        artifact_root = dashboard_bundle
    elif (
        not (resolved_root / "data" / "features_df.csv").exists()
        and fallback_artifact_root.exists()
    ):
        artifact_root = fallback_artifact_root

    edgelists_dir = artifact_root / "data" / "edgelists"
    dashboard_edgelist = edgelists_dir / "edgelist_dashboard_users.csv"
    corpus_edgelist = edgelists_dir / "edgelist_full.csv"
    resolved_edgelist_path = (
        dashboard_edgelist if dashboard_edgelist.exists() else corpus_edgelist
    )

    paths = PathsConfig(
        repo_root=resolved_root,
        artifact_root=artifact_root,
        dashboard_dir=resolved_root / "dashboard",
        features_path=artifact_root / "data" / "features_df.csv",
        full_edgelist_path=resolved_edgelist_path,
        experiments_dir=artifact_root / "training" / "models" / "experiments",
        training_models_dir=artifact_root / "training" / "models",
    )

    model_families = (
        ModelFamilyConfig(
            key="autoencoder",
            label="Autoencoder",
            file_suffix=".keras",
            summary=(
                "An unsupervised user encoder that learns compressed taste profiles by "
                "reconstructing listening features."
            ),
        ),
        ModelFamilyConfig(
            key="siamese",
            label="Siamese Network",
            file_suffix=".pt",
            summary=(
                "A supervised pairwise embedding model trained to pull future-aligned "
                "users together in representation space."
            ),
        ),
    )

    demo_users = (
        DemoUserConfig(
            key="night_owl",
            alias="Sean",
            blurb="The most night-heavy listening pattern in the cohort.",
            selection_strategy="max",
            columns=("temporal_night_ratio",),
        ),
        DemoUserConfig(
            key="high_energy",
            alias="Daniel",
            blurb="The highest average-energy listener in the saved feature table.",
            selection_strategy="max",
            columns=("avg_energy",),
        ),
        DemoUserConfig(
            key="high_diversity",
            alias="Timothy",
            blurb="The broadest genre explorer in the demo set.",
            selection_strategy="max",
            columns=("genre_unique_count",),
        ),
        DemoUserConfig(
            key="high_hipster",
            alias="Roger",
            blurb="A listener with the strongest underground / long-tail profile.",
            selection_strategy="max",
            columns=("hipster_gap",),
        ),
        DemoUserConfig(
            key="median_profile",
            alias="Pierce",
            blurb="A representative listener close to the cohort median on core taste axes.",
            selection_strategy="median_distance",
            columns=("avg_energy", "genre_entropy", "avg_tempo"),
        ),
    )

    semantic_groups = (
        SemanticGroupConfig(
            key="energy",
            label="Energy",
            description="How intense and high-motion the listening profile feels overall.",
            story_lead="Their listening momentum lives in the same lane, which creates an easy overlap in pace.",
            signals=(
                SemanticSignalConfig("avg_energy"),
                SemanticSignalConfig("pct_high_energy"),
                SemanticSignalConfig("pct_low_energy", invert=True),
            ),
        ),
        SemanticGroupConfig(
            key="mood",
            label="Mood",
            description="A composite of valence and emotional brightness in the music they choose.",
            story_lead="Their emotional center of gravity is close enough to make the pair feel tonally consistent.",
            signals=(
                SemanticSignalConfig("avg_valence"),
                SemanticSignalConfig("pct_happy_tracks"),
                SemanticSignalConfig("pct_sad_tracks", invert=True),
            ),
        ),
        SemanticGroupConfig(
            key="tempo",
            label="Tempo",
            description="How fast-paced the pair's listening history tends to be.",
            story_lead="They return to similar BPM territory, which hints at compatible movement and mood.",
            signals=(
                SemanticSignalConfig("avg_tempo"),
                SemanticSignalConfig("pct_fast_tracks"),
                SemanticSignalConfig("pct_slow_tracks", invert=True),
            ),
        ),
        SemanticGroupConfig(
            key="night_listening",
            label="Night Listening",
            description="How much the user leans into late-night sessions and after-hours listening.",
            story_lead="Both users show a similar after-hours cadence, which is a natural narrative hook for the product.",
            signals=(
                SemanticSignalConfig("temporal_night_ratio"),
                SemanticSignalConfig("night_energy_mean"),
                SemanticSignalConfig("night_valence_mean"),
            ),
        ),
        SemanticGroupConfig(
            key="genre_breadth",
            label="Genre Breadth",
            description="How wide the user ranges across genres without collapsing into a single lane.",
            story_lead="They balance familiarity and exploration in similar ways, which makes discovery feel mutual instead of one-sided.",
            signals=(
                SemanticSignalConfig("genre_unique_count"),
                SemanticSignalConfig("genre_entropy"),
                SemanticSignalConfig("genre_evenness"),
            ),
        ),
        SemanticGroupConfig(
            key="artist_exploration",
            label="Artist Exploration",
            description="How many artists they explore and how concentrated their repeat listening becomes.",
            story_lead="Their artist habits suggest a similar appetite for finding new names versus replaying favorites.",
            signals=(
                SemanticSignalConfig("nunique_artist"),
                SemanticSignalConfig("artist_concentration_index", invert=True),
                SemanticSignalConfig("one_hit_wonder"),
            ),
        ),
        SemanticGroupConfig(
            key="underground_lean",
            label="Underground Lean",
            description="How strongly the listener skews toward deeper cuts and non-mainstream tracks.",
            story_lead="Both users lean away from the obvious hits, which creates a strong 'deep cuts in common' story.",
            signals=(
                SemanticSignalConfig("hipster_gap"),
                SemanticSignalConfig("pct_underground_tracks"),
                SemanticSignalConfig("pct_viral_tracks", invert=True),
            ),
        ),
        SemanticGroupConfig(
            key="loyalty",
            label="Loyalty",
            description="How much they commit to repeat listens, early favorites, and familiar comfort zones.",
            story_lead="Their repeat-listen behavior moves together, making the pair feel steady rather than random.",
            signals=(
                SemanticSignalConfig("loyal_track_count"),
                SemanticSignalConfig("early_loyal_ratio"),
                SemanticSignalConfig("favorite_genre_ratio"),
            ),
        ),
    )

    ui = UIConfig(
        app_title="Spotdate Match Dashboard",
        app_subtitle="From listening history to explainable pair stories",
        hero_intro_heading="Because a bad playlist is a dealbreaker.",
        hero_intro_body=(
            "Spotdate transforms Spotify listening data into meaningful connections. "
            "By analyzing track-level audio features across 20,000+ users, we use an "
            "autoencoder to map complex musical tastes and predict compatibility. "
            "It's more than a recap. It's a data-driven way to find your perfect sonic match."
        ),
        app_description=(
            "This dashboard turns saved model artifacts into a product-facing demo: "
            "pick one demo user, choose a model family, and inspect the pair-specific "
            "story we could show in a real product."
        ),
        implementation_section_title="Implementation Ideas",
        top_match_count=5,
        flow_card_count=3,
        radar_axis_count=5,
    )

    style = StyleConfig(
        background="#08111f",
        panel_background="#0f1b2d",
        text_primary="#f4f7fb",
        text_muted="#9db0c8",
        accent="#4dd7a8",
        accent_secondary="#f6508f",
        accent_tertiary="#5ec2ff",
    )

    return DashboardConfig(
        paths=paths,
        model_selection=ModelSelectionConfig(metric="avg_score"),
        model_families=model_families,
        demo_users=demo_users,
        semantic_groups=semantic_groups,
        ui=ui,
        style=style,
    )


CONFIG = build_config()
