#!/usr/bin/env pkgx uv run

"""
Sample a large listening history CSV by complete users up to a size limit.

The script:
- reads an input CSV with a given delimiter (default `;`)
- treats `user_id` (first column) as the grouping key
- picks a random subset of users such that the total bytes of all their rows
  plus the header do not exceed a configured maximum (default 500 MiB)
- writes all rows for the selected users to an output CSV

Two-pass approach:
1) First pass: compute the total byte size per user (using the raw line length).
2) Second pass: write only rows whose `user_id` is in the selected user set.

Usage example:

    chmod +x data-loading/sample_listening_history_users.py
    ./data-loading/sample_listening_history_users.py \\
        --input path/to/listening_history.csv \\
        --output path/to/listening_history_sample.csv \\
        --max-size-mb 500
"""

from __future__ import annotations

import argparse
import random
from collections import defaultdict
from typing import Dict, Iterable, Set, Tuple


BYTES_IN_MIB = 1024 * 1024


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Sample a listening history CSV by full users up to a maximum file size "
            "(approximate, based on input line lengths)."
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
        help="Path to the output CSV file.",
    )
    parser.add_argument(
        "--max-size-mb",
        type=float,
        default=500.0,
        help="Maximum output size in MiB (default: 500).",
    )
    parser.add_argument(
        "--delimiter",
        "-d",
        default=";",
        help="CSV delimiter used in the input file (default: ';').",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for user sampling (default: 42).",
    )
    return parser.parse_args()


def collect_user_sizes(
    input_path: str,
    delimiter: str,
) -> Tuple[str, int, Dict[str, int], int]:
    """
    First pass over the input file.

    Returns:
    - header line (including newline, if present)
    - header size in bytes
    - mapping of user_id -> total byte size of all their rows
    - total number of non-header, non-empty rows
    """
    user_sizes: Dict[str, int] = defaultdict(int)
    total_rows = 0

    with open(input_path, "r", encoding="utf-8") as infile:
        header = infile.readline()
        header_bytes = len(header.encode("utf-8")) if header else 0

        for line in infile:
            if not line.strip():
                continue
            # Assumes user_id is the first column.
            parts = line.split(delimiter, 1)
            user_id = parts[0]

            line_bytes = len(line.encode("utf-8"))
            user_sizes[user_id] += line_bytes
            total_rows += 1

    return header, header_bytes, dict(user_sizes), total_rows


def select_users_under_size(
    user_sizes: Dict[str, int],
    header_bytes: int,
    max_size_bytes: int,
    seed: int,
) -> Tuple[Set[str], int]:
    """
    Select a random subset of users whose total byte size fits under max_size_bytes.

    Uses a greedy algorithm on a random permutation of users.
    """
    rng = random.Random(seed)
    users = list(user_sizes.items())
    rng.shuffle(users)

    selected_users: Set[str] = set()
    accumulated_bytes = header_bytes

    for user_id, size in users:
        if accumulated_bytes + size > max_size_bytes:
            continue
        selected_users.add(user_id)
        accumulated_bytes += size

    return selected_users, accumulated_bytes


def write_sample(
    input_path: str,
    output_path: str,
    delimiter: str,
    selected_users: Iterable[str],
) -> Tuple[int, int]:
    """
    Second pass over the input file. Writes only rows whose user_id is selected.

    Returns:
    - number of users seen while writing
    - number of rows written (excluding header)
    """
    selected_users_set = set(selected_users)
    seen_users: Set[str] = set()
    written_rows = 0

    with open(input_path, "r", encoding="utf-8") as infile, open(
        output_path,
        "w",
        encoding="utf-8",
        newline="",
    ) as outfile:
        header = infile.readline()
        if header:
            outfile.write(header)

        for line in infile:
            if not line.strip():
                continue
            parts = line.split(delimiter, 1)
            user_id = parts[0]
            if user_id not in selected_users_set:
                continue
            outfile.write(line)
            written_rows += 1
            seen_users.add(user_id)

    return len(seen_users), written_rows


def main() -> None:
    args = parse_args()
    max_size_bytes = int(args.max_size_mb * BYTES_IN_MIB)

    (
        header,
        header_bytes,
        user_sizes,
        total_rows,
    ) = collect_user_sizes(args.input, args.delimiter)

    if not header:
        raise SystemExit("Input file appears to be empty or missing a header.")

    if not user_sizes:
        raise SystemExit("No data rows found in the input file.")

    selected_users, estimated_bytes = select_users_under_size(
        user_sizes=user_sizes,
        header_bytes=header_bytes,
        max_size_bytes=max_size_bytes,
        seed=args.seed,
    )

    if not selected_users:
        raise SystemExit(
            "No users could be selected under the specified size limit. "
            "Try increasing --max-size-mb.",
        )

    unique_users = len(user_sizes)

    print(
        f"Loaded {total_rows} rows across {unique_users} users from '{args.input}'.",
    )
    print(
        f"Selected {len(selected_users)} users; "
        f"estimated output size (bytes): {estimated_bytes:,} "
        f"({estimated_bytes / BYTES_IN_MIB:.2f} MiB).",
    )

    written_users, written_rows = write_sample(
        input_path=args.input,
        output_path=args.output,
        delimiter=args.delimiter,
        selected_users=selected_users,
    )

    print(
        f"Wrote {written_rows} rows for {written_users} users to '{args.output}'.",
    )


if __name__ == "__main__":
    main()

