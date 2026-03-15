import pandas as pd

from utils.logger import get_logger

logger = get_logger("feature_extraction.audio_features", 20)


def extract(listening_history: pd.DataFrame) -> pd.DataFrame:
    """
    Placeholder for advanced audio feature aggregation.

    Expected behavior for this module:
    - Input: raw listening_history with audio descriptors or embeddings.
    - Output: dataframe indexed by user_id with audio_* feature columns.
    """
    df = listening_history.copy()

    # --- AVG AND VARIANCE OF AUDIO FEATURES ---
    for feature in [
        "valence",
        "energy",
        "danceability",
        "popularity",
        "acousticness",
        "instrumentalness",
        "liveness",
        "loudness",
        "speechiness",
        "tempo",
        "key",
    ]:
        df[f"avg_{feature}"] = df.groupby("user_id")[feature].transform("mean")
        df[f"variance_{feature}"] = df.groupby("user_id")[feature].transform("var")

    df["explicit_mode"] = df.groupby("user_id")["explicit"].transform(
        lambda x: x.mode()[0]
    )

    # --- EMOTIONAL STATE ---
    df["emotional_state"] = df.groupby("user_id")["valence"].transform("median")
    df["emotional_state"] = pd.cut(
        df["emotional_state"],
        bins=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
        labels=["depressed", "sad", "neutral", "happy", "euphoric"],
        include_lowest=True,
    )

    # --- DAY AND NIGHT FEATURES ---
    df["listen_timestamp"] = pd.to_datetime(df["listen_timestamp"])
    df = df.sort_values(["user_id", "listen_timestamp"])
    df["hour"] = df["listen_timestamp"].dt.hour

    day = df[df["hour"].between(6, 17)]
    night = df[df["hour"].between(18, 23) | df["hour"].between(0, 5)]

    day_night_features = []
    for feature in ["valence", "energy", "tempo", "danceability", "loudness"]:
        day_mean = day.groupby("user_id")[feature].mean().rename(f"day_{feature}_mean")
        night_mean = (
            night.groupby("user_id")[feature].mean().rename(f"night_{feature}_mean")
        )
        day_night_features.append(day_mean)
        day_night_features.append(night_mean)

    day_night_df = pd.concat(day_night_features, axis=1).reset_index()
    df = df.merge(day_night_df, on="user_id", how="left")

    # --- % DISTRIBUTION OF FEATURES ---
    df["pct_zero_popularity"] = df.groupby("user_id")["popularity"].transform(
        lambda x: (x == 0).mean()
    )
    df["pct_viral_tracks"] = df.groupby("user_id")["popularity"].transform(
        lambda x: (x > 80).mean()
    )
    df["pct_underground_tracks"] = df.groupby("user_id")["popularity"].transform(
        lambda x: (x < 20).mean()
    )
    df["pct_explicit"] = df.groupby("user_id")["explicit"].transform("mean")
    df["pct_fast_tracks"] = df.groupby("user_id")["tempo"].transform(
        lambda x: (x > 150).mean()
    )
    df["pct_slow_tracks"] = df.groupby("user_id")["tempo"].transform(
        lambda x: (x < 80).mean()
    )
    df["pct_high_energy"] = df.groupby("user_id")["energy"].transform(
        lambda x: (x > 0.7).mean()
    )
    df["pct_low_energy"] = df.groupby("user_id")["energy"].transform(
        lambda x: (x < 0.3).mean()
    )
    df["pct_happy_tracks"] = df.groupby("user_id")["valence"].transform(
        lambda x: (x > 0.6).mean()
    )
    df["pct_sad_tracks"] = df.groupby("user_id")["valence"].transform(
        lambda x: (x < 0.4).mean()
    )
    df["pct_live"] = df.groupby("user_id")["liveness"].transform(
        lambda x: (x > 0.8).mean()
    )
    df["pct_speech"] = df.groupby("user_id")["speechiness"].transform(
        lambda x: (x > 0.66).mean()
    )

    # --- EVOLUTION OF FEATURES ---
    df = df.sort_values(["user_id", "listen_timestamp"])
    df["track_rank"] = df.groupby("user_id").cumcount()
    df["total_tracks"] = df.groupby("user_id")["track_rank"].transform("max")
    df["listening_phase"] = (df["track_rank"] / df["total_tracks"] > 0.5).astype(int)

    for feature in ["valence", "energy", "tempo", "danceability", "acousticness"]:
        early = df[df["listening_phase"] == 0].groupby("user_id")[feature].mean()
        late = df[df["listening_phase"] == 1].groupby("user_id")[feature].mean()
        df[f"{feature}_evolution"] = df["user_id"].map(late - early)

    # --- FINAL: collapse to one row per user ---
    cols_to_keep = [
        "user_id",
        "avg_valence",
        "avg_energy",
        "avg_danceability",
        "avg_popularity",
        "avg_acousticness",
        "avg_instrumentalness",
        "avg_liveness",
        "avg_loudness",
        "avg_speechiness",
        "avg_tempo",
        "avg_key",
        "explicit_mode",
        "variance_valence",
        "variance_energy",
        "variance_danceability",
        "variance_popularity",
        "variance_acousticness",
        "variance_instrumentalness",
        "variance_liveness",
        "variance_loudness",
        "variance_speechiness",
        "variance_tempo",
        "variance_key",
        "emotional_state",
        "pct_zero_popularity",
        "pct_viral_tracks",
        "pct_underground_tracks",
        "pct_explicit",
        "pct_fast_tracks",
        "pct_slow_tracks",
        "pct_high_energy",
        "pct_low_energy",
        "pct_happy_tracks",
        "pct_sad_tracks",
        "pct_live",
        "pct_speech",
        "night_energy_mean",
        "day_energy_mean",
        "night_valence_mean",
        "day_valence_mean",
        "night_tempo_mean",
        "day_tempo_mean",
        "night_danceability_mean",
        "day_danceability_mean",
        "night_loudness_mean",
        "day_loudness_mean",
        "valence_evolution",
        "energy_evolution",
        "tempo_evolution",
        "danceability_evolution",
        "acousticness_evolution",
    ]

    df = df[cols_to_keep].drop_duplicates("user_id").reset_index(drop=True)
    df = df.set_index("user_id")
    df.index.name = "user_id"

    logger.info(f"Audio features extracted for {len(df)} users.")
    return df
