import argparse
import os
from functools import reduce

import pandas as pd

from training.feature_extraction._contract import ensure_user_index
from training.feature_extraction.extractors import EXTRACTORS
from utils.logger import get_logger

logger = get_logger("feature_extraction", 20)

CUTOFF_TIMESTAMP = "2012-03-26 13:30:08+00:00"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Take an input listening history and return a feature enriched dataset"
        ),
    )
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Path to the input CSV file.",
    )
    parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Path to the output CSV file (or an output directory).",
    )
    parser.add_argument(
        "--only",
        choices=[name for name, _ in EXTRACTORS],
        default=None,
        help="Run only a single feature extractor (by name).",
    )
    parser.add_argument(
        "--print",
        dest="print_result",
        action="store_true",
        help="Print the resulting user-level dataframe to stdout.",
    )
    parser.add_argument(
        "--print-rows",
        type=int,
        default=25,
        help="Number of rows to print when --print is set (default: 25).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = args.input
    output = args.output
    only = args.only
    print_result = args.print_result
    print_rows = args.print_rows

    logger.info("Loading listening history from %s", input_path)
    listening_history = pd.read_csv(input_path, delimiter=";")

    logger.info("Converting listen_timestamp to UTC-aware datetime")
    listening_history["listen_timestamp"] = pd.to_datetime(
        listening_history["listen_timestamp"], errors="coerce", utc=True
    )
    cutoff_date = pd.Timestamp(CUTOFF_TIMESTAMP)

    logger.info("Using fixed cutoff date: %s", cutoff_date)
    past_df = listening_history[listening_history["listen_timestamp"] <= cutoff_date]

    feature_dfs = []
    for name, extract_fn in EXTRACTORS:
        if only is not None and name != only:
            continue
        logger.info("Running feature extractor: %s", name)
        features = extract_fn(past_df)
        features = ensure_user_index(features)
        feature_dfs.append(features)

    if not feature_dfs:
        logger.warning("No feature extractors configured; writing empty features_df.")
        user_df = pd.DataFrame()
    else:
        user_df = reduce(lambda left, right: left.join(right, how="outer"), feature_dfs)
        user_df = user_df.fillna(0)

    if output.endswith(".csv"):
        output_path = output
    else:
        os.makedirs(output, exist_ok=True)
        output_path = f"{output}/features_df.csv"
    logger.info("Writing features to %s", output_path)
    user_df.to_csv(output_path)

    if print_result:
        with pd.option_context("display.max_rows", print_rows, "display.width", 200):
            print(user_df.head(print_rows))


if __name__ == "__main__":
    main()
