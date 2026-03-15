import pandas as pd

from utils.logger import get_logger

logger = get_logger("feature_extraction.temporal", 20)


def _ensure_hour_column(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure there is an `hour` column derived from `listen_timestamp`."""

    if "hour" in df.columns:
        return df

    if "listen_timestamp" not in df.columns:
        return df

    df = df.copy()
    df["listen_timestamp"] = pd.to_datetime(
        df["listen_timestamp"], errors="coerce", utc=True
    )
    df["hour"] = df["listen_timestamp"].dt.hour
    return df


def _hourly_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Return per-user hourly listen ratio features."""

    user_hour_dist = (
        df.groupby(["user_id", "hour"]).size().unstack(fill_value=0)
    )

    total_listens = user_hour_dist.sum(axis=1).replace({0: 1})
    hour_ratio = user_hour_dist.div(total_listens, axis=0)

    return hour_ratio.add_prefix("temporal_h_dist_")


def peak_hour(df: pd.DataFrame, listening_history: pd.DataFrame) -> pd.DataFrame:
    """Compute each user's peak listening hour."""

    user_hour_dist = (
        listening_history.groupby(["user_id", "hour"]).size().unstack(fill_value=0)
    )

    peak_hours = user_hour_dist.idxmax(axis=1)
    df["temporal_peak_hour"] = peak_hours

    return df


def night_ratio(df: pd.DataFrame, listening_history: pd.DataFrame) -> pd.DataFrame:
    """Compute ratio of listens between 0-5am vs total listens."""

    user_hour_dist = (
        listening_history.groupby(["user_id", "hour"]).size().unstack(fill_value=0)
    )

    night_cols = [h for h in range(6) if h in user_hour_dist.columns]
    night_counts = user_hour_dist[night_cols].sum(axis=1)
    total_counts = user_hour_dist.sum(axis=1).replace({0: 1})
    night_ratio_series = night_counts / total_counts

    df["temporal_night_ratio"] = night_ratio_series

    return df


def _build_session_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build per-user session-derived temporal features."""

    if "listen_timestamp" not in df.columns:
        return pd.DataFrame({"user_id": df["user_id"].unique()}).set_index("user_id")

    df = df.copy()
    df["listen_timestamp"] = pd.to_datetime(
        df["listen_timestamp"], errors="coerce", utc=True
    )

    df = df.sort_values(["user_id", "listen_timestamp"]).reset_index(drop=True)

    df["time_since_last"] = df.groupby("user_id")["listen_timestamp"].diff()

    if "duration_ms" in df.columns:
        df["prev_duration_ms"] = df.groupby("user_id")["duration_ms"].shift(1)
        df["prev_duration_ms"] = pd.to_numeric(df["prev_duration_ms"], errors="coerce").fillna(0)
        df["prev_duration"] = pd.to_timedelta(df["prev_duration_ms"], unit="ms")
        df["idle_gap"] = df["time_since_last"] - df["prev_duration"]
    else:
        df["idle_gap"] = df["time_since_last"]

    is_new_session = (
        df["time_since_last"].isna() | (df["idle_gap"] > pd.Timedelta(minutes=10))
    )
    df["session_id"] = is_new_session.cumsum()

    session_sizes = df.groupby("session_id").size()
    valid_sessions = session_sizes[session_sizes >= 3].index
    df_sessions = df[df["session_id"].isin(valid_sessions)].copy()

    if df_sessions.empty:
        return pd.DataFrame({"user_id": df["user_id"].unique()}).set_index("user_id")

    session_features = df_sessions.groupby("session_id").agg(
        user_id=("user_id", "first"),
        session_start=("listen_timestamp", "min"),
        track_count=("track_name", "count"),
        artist_count=("artist_name", "nunique"),
        avg_energy=("energy", "mean"),
        avg_valence=("valence", "mean"),
        avg_acousticness=("acousticness", "mean"),
        avg_danceability=("danceability", "mean"),
    )

    session_features["artist_diversity_ratio"] = (
        session_features["artist_count"] / session_features["track_count"]
    )

    first_energy = df_sessions.groupby("session_id")["energy"].first()
    last_energy = df_sessions.groupby("session_id")["energy"].last()
    session_features["energy_trajectory"] = last_energy - first_energy

    session_features["session_hour"] = session_features["session_start"].dt.hour

    user_session = session_features.groupby("user_id").agg(
        temporal_total_sessions=("track_count", "count"),
        temporal_avg_session_track_count=("track_count", "mean"),
        temporal_avg_artist_diversity_ratio=("artist_diversity_ratio", "mean"),
        temporal_avg_energy_trajectory=("energy_trajectory", "mean"),
        temporal_avg_session_hour=("session_hour", "mean"),
    )

    return user_session


def _build_loyalty_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute a simple loyalty/early-adopter profile per user."""

    if "track_name" not in df.columns:
        return pd.DataFrame({"user_id": df["user_id"].unique()}).set_index("user_id")

    popular_tracks = df.groupby("track_name")["user_id"].nunique()
    popular_tracks = popular_tracks[popular_tracks >= 10].index
    df_popular = df[df["track_name"].isin(popular_tracks)].copy()

    if df_popular.empty:
        return pd.DataFrame({"user_id": df["user_id"].unique()}).set_index("user_id")

    user_track_counts = (
        df_popular.groupby(["user_id", "track_name"]).size().reset_index(name="listen_count")
    )
    loyal_pairs = user_track_counts[user_track_counts["listen_count"] >= 5][["user_id", "track_name"]]
    df_loyal = df_popular.merge(loyal_pairs, on=["user_id", "track_name"], how="inner")

    if df_loyal.empty:
        return pd.DataFrame({"user_id": df["user_id"].unique()}).set_index("user_id")

    df_loyal["listen_timestamp"] = pd.to_datetime(
        df_loyal["listen_timestamp"], errors="coerce", utc=True
    )

    min_ts = df_loyal.groupby("track_name")["listen_timestamp"].transform("min")
    df_loyal["time_delta"] = (df_loyal["listen_timestamp"] - min_ts).dt.total_seconds()

    def mark_early(group: pd.DataFrame) -> pd.DataFrame:
        if group.empty:
            group["is_early"] = 0
            return group
        threshold = group["time_delta"].quantile(0.15)
        group["is_early"] = (group["time_delta"] <= threshold).astype(int)
        return group

    df_loyal = df_loyal.groupby("track_name", group_keys=False).apply(mark_early)

    user_profile = df_loyal.groupby("user_id").agg(
        loyal_track_count=("track_name", "nunique"),
        early_loyal_listens=("is_early", "sum"),
    )

    user_profile["early_loyal_ratio"] = (
        user_profile["early_loyal_listens"] / user_profile["loyal_track_count"]
    )

    user_profile["user_type_loyal"] = user_profile["early_loyal_ratio"].apply(
        lambda x: "Loyal Trendsetter" if x > 0.2 else "Follower/Others"
    )

    return user_profile


def extract(listening_history: pd.DataFrame) -> pd.DataFrame:
    """Compute all temporal features for each user.

    Returns a dataframe indexed by user_id with temporal_* feature columns.
    """
    logger.info("Extracting temporal features...")

    if listening_history is None or listening_history.empty:
        return pd.DataFrame(index=pd.Index([], name="user_id"))

    df = listening_history.copy()
    df = _ensure_hour_column(df)

    user_ids = df["user_id"].dropna().unique()
    result = pd.DataFrame(index=user_ids)
    result.index.name = "user_id"

    result = peak_hour(result, df)
    result = night_ratio(result, df)

    hourly_dist = _hourly_distribution(df)
    result = result.join(hourly_dist, how="left")

    session_feats = _build_session_features(df)
    result = result.join(session_feats, how="left")

    loyalty_feats = _build_loyalty_features(df)
    result = result.join(loyalty_feats, how="left")

    return result.fillna(0)
