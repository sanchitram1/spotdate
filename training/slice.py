#!/usr/bin/env pkgx uv run

"""Split a listening history CSV into past and future windows.

The past window is used for feature extraction and model training.
The future window is used for label generation (clustering.py, heuristics.py)
to approximate ground-truth match quality.
"""

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from utils.logger import get_logger

logger = get_logger("slice", 20)


@dataclass(frozen=True)
class SliceConfig:
    cutoff_timestamp: str = "2012-03-26 13:30:08+00:00"
    timestamp_col: str = "listen_timestamp"
    delimiter: str = ";"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Split a listening history CSV into past and future windows "
            "based on a cutoff timestamp."
        ),
    )
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Path to the input listening history CSV file.",
    )
    parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Directory where past/future CSVs will be written.",
    )
    return parser.parse_args()


def slice_listening_history(
    listening_history: pd.DataFrame, *, config: SliceConfig
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split listening history into past and future DataFrames."""
    col = config.timestamp_col

    if col not in listening_history.columns:
        raise ValueError(f"Missing required column: {col}")

    listening_history[col] = pd.to_datetime(
        listening_history[col], errors="coerce", utc=True
    )

    before = len(listening_history)
    listening_history = listening_history.dropna(subset=[col])
    dropped = before - len(listening_history)
    if dropped:
        logger.warning("Dropped %d rows with unparseable %s.", dropped, col)

    cutoff = pd.Timestamp(config.cutoff_timestamp)
    logger.info("Cutoff timestamp: %s", cutoff)

    past_df = listening_history[listening_history[col] <= cutoff]
    future_df = listening_history[listening_history[col] > cutoff]

    past_users = set(past_df["user_id"].unique())
    future_users = set(future_df["user_id"].unique())
    shared_users = past_users & future_users

    past_only = len(past_users - shared_users)
    future_only = len(future_users - shared_users)
    if past_only or future_only:
        logger.warning(
            "Filtering to %d shared users. Dropping %d past-only and %d future-only.",
            len(shared_users),
            past_only,
            future_only,
        )

    past_df = past_df[past_df["user_id"].isin(shared_users)]
    future_df = future_df[future_df["user_id"].isin(shared_users)]

    logger.info(
        "Split complete. past=%d rows (%d users), future=%d rows (%d users)",
        len(past_df),
        past_df["user_id"].nunique(),
        len(future_df),
        future_df["user_id"].nunique(),
    )

    return past_df, future_df


def main() -> None:
    args = parse_args()
    config = SliceConfig()

    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Reading listening history from %s", input_path)
    listening_history = pd.read_csv(input_path, delimiter=config.delimiter)
    logger.info("Loaded %d rows, %d users", len(listening_history), listening_history["user_id"].nunique())

    past_df, future_df = slice_listening_history(listening_history, config=config)

    past_path = output_dir / "past_listening_history.csv"
    future_path = output_dir / "future_listening_history.csv"

    past_df.to_csv(past_path, sep=config.delimiter, index=False)
    logger.info("Wrote past slice to %s", past_path)

    future_df.to_csv(future_path, sep=config.delimiter, index=False)
    logger.info("Wrote future slice to %s", future_path)


if __name__ == "__main__":
    main()
