#!/usr/bin/env pkgx uv run --with pandas
import pandas as pd


def peak_hour(df: pd.DataFrame, listening_history: pd.DataFrame) -> pd.DataFrame:
    """
    Generate identifier columns for whether that user spent the max amount of time
    listening to songs in that specific hour
    """
    # peak_hours = user_hour_dist.idxmax(axis=1)
    return df


def night_ratio(df: pd.DataFrame, listening_history: pd.DataFrame) -> pd.DataFrame:
    """
    A ratio between the number of songs listened to between 0-5am vs. all songs listened
    to
    """
    user_hour_dist = (
        listening_history.groupby(["user_id", "hour"]).size().unstack(fill_value=0)
    )

    night_cols = [h for h in range(6) if h in user_hour_dist.columns]
    night_counts = user_hour_dist[night_cols].sum(axis=1)
    total_counts = user_hour_dist.sum(axis=1)
    night_ratio = night_counts / total_counts

    df["night_ratio"] = night_ratio

    return df


def follower_trendsetter():
    """
    EXPLAIN WHAT THE FUNCTION IS HERE
    """
    # # 1. 计算每首歌的全局首听时间 (作为基准)
    # track_first_timestamp = (
    #     df_subset.groupby("track_name")["listen_timestamp"].min().reset_index()
    # )
    # track_first_timestamp.columns = ["track_name", "global_first_time"]

    # # 2. 合并回原表并计算“时间差”
    # df_analysis = df_subset.merge(track_first_timestamp, on="track_name")
    # # 计算这首歌从出现到该用户听的时间差 (秒或天)
    # df_analysis["time_delta"] = (
    #     df_analysis["listen_timestamp"] - df_analysis["global_first_time"]
    # ).dt.total_seconds()

    # # 3. 标记 Early (这里简化逻辑：在该歌所有记录中时间排序前15%)
    # def mark_early(group):
    #     threshold = group["time_delta"].quantile(0.15)
    #     group["is_early"] = (group["time_delta"] <= threshold).astype(int)
    #     return group

    # df_labeled = df_analysis.groupby("track_name").apply(mark_early)

    # # 4. Map 到 User Level
    # user_profile = df_labeled.groupby("user_id").agg(
    #     total_listens=("is_early", "count"), early_listens=("is_early", "sum")
    # )
    # user_profile["early_discovery_ratio"] = (
    #     user_profile["early_listens"] / user_profile["total_listens"]
    # )

    # # 5. 最终打标
    # user_profile["user_type"] = user_profile["early_discovery_ratio"].apply(
    #     lambda x: "Trendsetter" if x > 0.2 else "Follower"
    # )

    pass


def main(df: pd.DataFrame, listening_history: pd.DataFrame) -> pd.DataFrame:
    """
    Inputs:
      - df: the input dataframe
      - listening_history: the actual raw data

    Return:
      - the dataframe with all temporal features
    """
    df_with_night_ratio = night_ratio(df)

    return df_with_night_ratio
