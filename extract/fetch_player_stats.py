"""
fetch_player_stats.py

Pulls player batting and pitching stats from Fangraphs via pybaseball
for seasons 2021-2025 and writes to parquet.

Usage:
    python fetch_player_stats.py
    python fetch_player_stats.py --output /path/to/dir
    python fetch_player_stats.py --start 2021 --end 2025
"""

import argparse
import re
from datetime import datetime
from pathlib import Path
from typing import Final

import pandas as pd
from pybaseball import batting_stats, cache, pitching_stats

cache.enable()

OUTPUT_DIR: Final[Path] = Path("./data/parquet")
START_SEASON: Final[int] = 2021
END_SEASON: Final[int] = 2025

# Explicit rename map for known duplicate columns in pitching data.
# Fangraphs includes both a standard and a scaled/rate version of these.
# First occurrence keeps the base name, second gets a descriptive suffix.
PITCHING_DUPE_RENAMES = {
    "k_per_9_2": "k_per_9_minus",
    "bb_per_9_2": "bb_per_9_minus",
    "h_per_9_2": "h_per_9_minus",
    "hr_per_9_2": "hr_per_9_minus",
    "rs_per_9_2": "rs_per_9_minus",
    "era_2": "era_minus",
    "fip_2": "fip_minus",
    "xfip_2": "xfip_minus",
    "fb_pct_2": "fb_pct_pitch",
}

BATTING_RENAMES = {
    "1b": "singles",
    "2b": "doubles",
    "3b": "triples",
    "def": "def_runs",
}


def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    def clean(col: str) -> str:
        c = col.lower().strip()
        # Handle +/- prefix columns first (e.g. -wpa, +wpa)
        if c.startswith("-") or c.startswith("+"):
            c = ("minus" if c.startswith("-") else "plus") + "_" + c[1:]
        c = c.replace("%", "_pct")
        c = c.replace("+", "_plus")
        c = c.replace("-", "_")
        c = c.replace("/", "_per_")
        c = c.replace("(", "").replace(")", "")
        c = c.replace(" ", "_")
        c = re.sub(r"_+", "_", c)  # collapse multiple underscores
        c = c.strip("_")
        return c

    df.columns = [clean(c) for c in df.columns]

    # Deduplicate — append _2, _3 etc to collisions
    seen: dict[str, int] = {}
    new_cols: list[str] = []
    for c in df.columns:
        if c in seen:
            seen[c] += 1
            new_cols.append(f"{c}_{seen[c]}")
        else:
            seen[c] = 1
            new_cols.append(c)
    df.columns = new_cols

    bad = [c for c in df.columns if re.search(r"[^a-z0-9_]", c)]
    if bad:
        print(f"Warning: still problematic column names: {bad}")

    return df


def validate_year_range(start: int, end: int) -> None:
    current_year = datetime.now().year
    if start > end:
        raise ValueError(
            f"Invalid range: start year {start} is greater than end year {end}."
        )
    if start < 1871:
        raise ValueError(
            f"Invalid start year: {start}. Earliest supported year is 1871."
        )
    if end > current_year:
        raise ValueError(
            f"Invalid end year: {end}. End year cannot be greater than {current_year}."
        )


def fetch_batting(start: int, end: int) -> pd.DataFrame:
    print(f"Fetching batting stats {start}–{end}...")
    try:
        df = batting_stats(start, end, split_seasons=True, qual=1)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to fetch batting stats for seasons {start}-{end}."
        ) from exc

    df = clean_columns(df)
    df = df.rename(columns=BATTING_RENAMES)
    print(f"  {len(df)} rows, {len(df.columns)} columns")
    return df


def fetch_pitching(start: int, end: int) -> pd.DataFrame:
    print(f"Fetching pitching stats {start}–{end}...")
    try:
        df = pitching_stats(start, end, split_seasons=True, qual=1)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to fetch pitching stats for seasons {start}-{end}."
        ) from exc

    df = clean_columns(df)
    df = df.rename(columns=PITCHING_DUPE_RENAMES)
    print(f"  {len(df)} rows, {len(df.columns)} columns")
    return df


def main(output_dir: Path, start: int, end: int) -> None:
    validate_year_range(start, end)

    if output_dir.exists() and not output_dir.is_dir():
        raise NotADirectoryError(f"Output path is not a directory: {output_dir}")

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        raise RuntimeError(f"Failed to create output directory: {output_dir}") from exc

    batting = fetch_batting(start, end)
    out = output_dir / "batting.parquet"
    try:
        batting.to_parquet(out, index=False)
    except Exception as exc:
        raise RuntimeError(f"Failed to write batting parquet to {out}.") from exc
    print(f"✓ batting → {out}")

    pitching = fetch_pitching(start, end)
    out = output_dir / "pitching.parquet"
    try:
        pitching.to_parquet(out, index=False)
    except Exception as exc:
        raise RuntimeError(f"Failed to write pitching parquet to {out}.") from exc
    print(f"✓ pitching → {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch Fangraphs stats → parquet")
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--start", type=int, default=START_SEASON)
    parser.add_argument("--end", type=int, default=END_SEASON)
    args = parser.parse_args()

    main(args.output, args.start, args.end)
