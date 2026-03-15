import numpy as np
import pandas as pd

from utils.logger import get_logger

logger = get_logger("feature_extraction.genre", 20)


TOP_20_FEATURE_COLUMNS = [
    "user_id",
    "genre_unique_count",
    "genre_entropy",
    "favorite_genre_ratio",
    "top2_genre_ratio",
    "top3_genre_ratio",
    "dominant_genre_time_ratio",
    "avg_listening_time_per_genre",
    "favorite_genre_avg_energy",
    "favorite_genre_avg_valence",
    "favorite_genre_avg_popularity",
    "genre_evenness",
    "genre_hhi",
    "genre_gini_index",
    "second_genre_ratio",
    "third_genre_ratio",
    "top5_genre_ratio",
    "tail_genre_ratio",
    "singleton_genre_ratio",
]


def clean_genre_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and normalize listening history for genre feature extraction."""

    data = df.copy()
    data = data.dropna(subset=["user_id", "genre"])
    data["genre"] = data["genre"].astype(str).str.strip().str.lower()

    if "duration_ms" in data.columns:
        data["duration_ms"] = pd.to_numeric(
            data["duration_ms"], errors="coerce"
        ).fillna(0.0)
    else:
        data["duration_ms"] = 0.0

    for col in ["energy", "valence", "popularity"]:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")

    return data


def get_user_genre_counts(data: pd.DataFrame) -> pd.DataFrame:
    """Build user-genre listen counts and ratios."""

    user_genre_counts = (
        data.groupby(["user_id", "genre"])  # type: ignore[no-untyped-call]
        .size()
        .reset_index(name="listen_count")
    )

    total_listens = (
        user_genre_counts.groupby("user_id")["listen_count"]
        .sum()
        .reset_index(name="total_listens")
    )

    user_genre_counts = user_genre_counts.merge(total_listens, on="user_id", how="left")

    user_genre_counts["genre_ratio"] = (
        user_genre_counts["listen_count"] / user_genre_counts["total_listens"]
    )

    return user_genre_counts


def compute_genre_diversity_features(user_genre_counts: pd.DataFrame) -> pd.DataFrame:
    """Compute genre diversity features."""

    genre_unique_count = (
        user_genre_counts.groupby("user_id")["genre"]
        .nunique()
        .reset_index(name="genre_unique_count")
    )

    genre_entropy = (
        user_genre_counts.groupby("user_id")["genre_ratio"]
        .apply(lambda x: -(x * np.log(x + 1e-12)).sum())
        .reset_index(name="genre_entropy")
    )

    return genre_unique_count.merge(genre_entropy, on="user_id", how="left")


def compute_genre_preference_features(
    user_genre_counts: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compute genre preference features (favorite genre, top-n ratios)."""

    sorted_counts = user_genre_counts.sort_values(
        ["user_id", "listen_count", "genre"],
        ascending=[True, False, True],
    )

    favorite_genre_ratio = (
        sorted_counts.groupby("user_id")["genre_ratio"]
        .first()
        .reset_index(name="favorite_genre_ratio")
    )

    top2_genre_ratio = (
        sorted_counts.groupby("user_id")["genre_ratio"]
        .apply(lambda x: x.head(2).sum())
        .reset_index(name="top2_genre_ratio")
    )

    top3_genre_ratio = (
        sorted_counts.groupby("user_id")["genre_ratio"]
        .apply(lambda x: x.head(3).sum())
        .reset_index(name="top3_genre_ratio")
    )

    preference_features = favorite_genre_ratio.merge(
        top2_genre_ratio, on="user_id", how="left"
    ).merge(top3_genre_ratio, on="user_id", how="left")

    favorite_genre = (
        sorted_counts.groupby("user_id")["genre"]
        .first()
        .reset_index(name="favorite_genre")
    )

    return preference_features, favorite_genre


def compute_genre_duration_features(data: pd.DataFrame) -> pd.DataFrame:
    """Compute duration-based genre features."""

    user_genre_duration = (
        data.groupby(["user_id", "genre"])["duration_ms"]
        .sum()
        .reset_index(name="genre_duration_ms")
    )

    total_duration = (
        user_genre_duration.groupby("user_id")["genre_duration_ms"]
        .sum()
        .reset_index(name="total_duration_ms")
    )

    user_genre_duration = user_genre_duration.merge(
        total_duration, on="user_id", how="left"
    )

    dominant_genre_time_ratio = (
        user_genre_duration.groupby("user_id")
        .apply(
            lambda x: (
                x["genre_duration_ms"].max() / x["total_duration_ms"].iloc[0]
                if x["total_duration_ms"].iloc[0] > 0
                else 0.0
            )
        )
        .reset_index(name="dominant_genre_time_ratio")
    )

    avg_listening_time_per_genre = (
        user_genre_duration.groupby("user_id")["genre_duration_ms"]
        .mean()
        .reset_index(name="avg_listening_time_per_genre")
    )

    return dominant_genre_time_ratio.merge(
        avg_listening_time_per_genre, on="user_id", how="left"
    )


def compute_favorite_genre_audio_features(
    data: pd.DataFrame, favorite_genre: pd.DataFrame
) -> pd.DataFrame:
    """Compute average audio features for the user's favorite genre."""

    data_with_fav = data.merge(favorite_genre, on="user_id", how="left")

    favorite_rows = data_with_fav[
        data_with_fav["genre"] == data_with_fav["favorite_genre"]
    ].copy()

    feature_tables = []

    if "energy" in favorite_rows.columns:
        energy_features = (
            favorite_rows.groupby("user_id")["energy"]
            .mean()
            .reset_index(name="favorite_genre_avg_energy")
        )
        feature_tables.append(energy_features)

    if "valence" in favorite_rows.columns:
        valence_features = (
            favorite_rows.groupby("user_id")["valence"]
            .mean()
            .reset_index(name="favorite_genre_avg_valence")
        )
        feature_tables.append(valence_features)

    if "popularity" in favorite_rows.columns:
        popularity_features = (
            favorite_rows.groupby("user_id")["popularity"]
            .mean()
            .reset_index(name="favorite_genre_avg_popularity")
        )
        feature_tables.append(popularity_features)

    if not feature_tables:
        return pd.DataFrame({"user_id": data["user_id"].unique()})

    audio_features = feature_tables[0]
    for table in feature_tables[1:]:
        audio_features = audio_features.merge(table, on="user_id", how="left")

    return audio_features


def compute_genre_distribution_features(
    user_genre_counts: pd.DataFrame,
) -> pd.DataFrame:
    """Compute distribution-based genre statistics."""

    def gini(array):
        array = np.array(array, dtype=float)

        if array.size == 0:
            return 0.0

        if np.amin(array) < 0:
            array -= np.amin(array)

        array += 1e-12
        array = np.sort(array)
        index = np.arange(1, array.shape[0] + 1)
        n = array.shape[0]

        return np.sum((2 * index - n - 1) * array) / (n * np.sum(array))

    results = []

    for user_id, group in user_genre_counts.groupby("user_id"):
        ratios = group["genre_ratio"].values
        counts = group["listen_count"].values

        sorted_ratios = np.sort(ratios)[::-1]
        unique_genres = len(ratios)
        entropy = -(ratios * np.log(ratios + 1e-12)).sum()

        if unique_genres > 1:
            evenness = entropy / np.log(unique_genres)
        else:
            evenness = 0.0

        hhi = np.sum(ratios**2)
        second_ratio = sorted_ratios[1] if len(sorted_ratios) > 1 else 0.0
        third_ratio = sorted_ratios[2] if len(sorted_ratios) > 2 else 0.0
        top5_ratio = sorted_ratios[:5].sum()
        tail_ratio = sorted_ratios[3:].sum() if len(sorted_ratios) > 3 else 0.0
        singleton_ratio = (
            (counts == 1).sum() / unique_genres if unique_genres > 0 else 0.0
        )
        gini_index = gini(counts)

        results.append(
            {
                "user_id": user_id,
                "genre_evenness": evenness,
                "genre_hhi": hhi,
                "genre_gini_index": gini_index,
                "second_genre_ratio": second_ratio,
                "third_genre_ratio": third_ratio,
                "top5_genre_ratio": top5_ratio,
                "tail_genre_ratio": tail_ratio,
                "singleton_genre_ratio": singleton_ratio,
            }
        )

    return pd.DataFrame(results)


def build_genre_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build a complete user-level genre feature matrix."""

    data = clean_genre_data(df)
    user_genre_counts = get_user_genre_counts(data)

    diversity_features = compute_genre_diversity_features(user_genre_counts)
    preference_features, favorite_genre = compute_genre_preference_features(
        user_genre_counts
    )
    duration_features = compute_genre_duration_features(data)
    audio_features = compute_favorite_genre_audio_features(data, favorite_genre)
    distribution_features = compute_genre_distribution_features(user_genre_counts)

    genre_features = (
        diversity_features.merge(preference_features, on="user_id", how="left")
        .merge(duration_features, on="user_id", how="left")
        .merge(audio_features, on="user_id", how="left")
        .merge(distribution_features, on="user_id", how="left")
    )

    return genre_features.fillna(0)


def extract(listening_history: pd.DataFrame) -> pd.DataFrame:
    """Compute user-level genre features.

    Returns a dataframe indexed by user_id with genre_* feature columns.
    """
    logger.info("Extracting genre features...")

    if listening_history is None or listening_history.empty:
        return pd.DataFrame(index=pd.Index([], name="user_id"))

    genre_features = build_genre_features(listening_history)

    existing_top20_columns = [
        col for col in TOP_20_FEATURE_COLUMNS if col in genre_features.columns
    ]

    genre_features_top20 = genre_features[existing_top20_columns].copy()
    genre_features_top20 = genre_features_top20.set_index("user_id", drop=True)
    genre_features_top20.index.name = "user_id"

    return genre_features_top20
