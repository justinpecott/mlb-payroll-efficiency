"""
parse_payroll.py

Parses Fangraphs team payroll .xlsx files into three parquet files:
  - players.parquet        -- one row per player per team per season, with future year salaries as JSON
  - summary.parquet        -- one row per team per season (luxury tax total)
  - other_payments.parquet -- trade subsidies, buyouts, and luxury tax adjustments

Usage:
    python parse_payroll.py                        # parse all xlsx in DATA_DIR
    python parse_payroll.py --input /path/to/dir   # specify input directory
    python parse_payroll.py --output /path/to/dir  # specify output directory
"""

import argparse
import json
import re
from pathlib import Path
from typing import Final, cast

import pandas as pd

# --- Config ---
DATA_DIR: Final[Path] = Path("./data/payroll")
OUTPUT_DIR: Final[Path] = Path("./data/parquet")

PLAYER_SHEETS: Final[list[str]] = [
    "Guaranteed",
    "Eligible For Arb",
    "Not Yet Eligible For Arb",
    "No Longer On 40-Man Roster",
]

OTHER_PAYMENT_SHEETS: Final[list[str]] = [
    "Other Payments",
    "Other Luxury Tax Payments",
]

NON_SALARY_STRINGS: Final[set[str]] = {
    "FREE AGENT",
    "ARB 1",
    "ARB 2",
    "ARB 3",
    "ARB 4",
    "Pre-ARB",
    "",
}

ALL_YEARS: Final[list[int]] = list(range(2021, 2035))


# --- Helpers ---
def parse_dollars(val: object) -> float | None:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if str(val).strip() in NON_SALARY_STRINGS:
        return None
    try:
        return float(str(val).replace("$", "").replace(",", "").strip())
    except ValueError:
        return None


def extract_team_season(path: Path) -> tuple[str, int]:
    stem = path.stem
    year_match = re.search(r"(20\d{2})", stem)
    season = int(year_match.group(1)) if year_match else None
    team = re.split(r"[-_]", stem)[0] if season else stem

    if not season:
        raise ValueError(
            f"Couldn't parse season from '{path.name}'. "
            "Expected filename to include a year like 2024."
        )
    if not team:
        raise ValueError(
            f"Couldn't parse team from '{path.name}'. "
            "Expected filename to start with a team token before '-' or '_'."
        )

    return team, season


def future_years_as_json(
    row: pd.Series, season: int, year_cols: list[int]
) -> str | None:
    """
    Collect all forward-looking year columns (after the current season)
    into a JSON string: {"2026": 12000000.0, "2027": "FREE AGENT", ...}
    Useful for contract obligation analysis in dbt later.
    """
    future: dict[str, float | str] = {}
    for yr in year_cols:
        if yr <= season:
            continue
        val = parse_dollars(row.get(yr))
        raw = row.get(yr)
        if val is not None:
            future[str(yr)] = val
        elif isinstance(raw, str) and raw.strip():
            future[str(yr)] = raw.strip()
    return json.dumps(future) if future else None


# --- Parsers ---
def parse_players(path: Path, team: str, season: int) -> pd.DataFrame:
    xl = pd.ExcelFile(path)
    dfs = []

    for sheet in PLAYER_SHEETS:
        if sheet not in xl.sheet_names:
            continue

        df = cast(pd.DataFrame, xl.parse(sheet)).dropna(how="all")
        df = df[df["Player"].notna()].copy()

        year_cols = [c for c in ALL_YEARS if c in df.columns]

        dfs.append(
            pd.DataFrame(
                {
                    "player": df["Player"],
                    "age": pd.to_numeric(df["Age"], errors="coerce"),
                    "service_time": df["Service Time"].astype(str),
                    "player_id": df["playerId"].astype(str),
                    "contract": df["Contract"].astype(str).str.strip(),
                    "info": df["Info"].astype(str).str.strip().replace("nan", None),
                    "aav": df["AAV"].apply(parse_dollars),
                    "salary": df[season].apply(parse_dollars)
                    if season in df.columns
                    else None,
                    "future_salaries": df.apply(  # pyright: ignore[reportCallIssue]
                        lambda r: future_years_as_json(r, season, year_cols),  # pyright: ignore[reportArgumentType]
                        axis=1,
                    ),
                    "contract_status": sheet,
                    "team": team,
                    "season": season,
                    "source_file": path.name,
                }
            )
        )

    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


def parse_other_payments(path: Path, team: str, season: int) -> pd.DataFrame:
    xl = pd.ExcelFile(path)
    dfs = []

    for sheet in OTHER_PAYMENT_SHEETS:
        if sheet not in xl.sheet_names:
            continue

        df = cast(pd.DataFrame, xl.parse(sheet)).dropna(how="all")
        df = df[df["Description"].notna()].copy()

        year_cols = [c for c in ALL_YEARS if c in df.columns]

        dfs.append(
            pd.DataFrame(
                {
                    "description": df["Description"].astype(str).str.strip(),
                    "amount": df[season].apply(parse_dollars)
                    if season in df.columns
                    else None,
                    "future_amounts": df.apply(  # pyright: ignore[reportCallIssue]
                        lambda r: future_years_as_json(r, season, year_cols),  # pyright: ignore[reportArgumentType]
                        axis=1,
                    ),
                    "payment_type": sheet,
                    "team": team,
                    "season": season,
                    "source_file": path.name,
                }
            )
        )

    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


def parse_summary(path: Path, team: str, season: int) -> dict[str, object] | None:
    xl = pd.ExcelFile(path)
    if "Luxury Tax Payroll Estimate" not in xl.sheet_names:
        return None

    df = cast(pd.DataFrame, xl.parse("Luxury Tax Payroll Estimate")).dropna(how="all")
    if season not in df.columns:
        return None

    total_row = df[
        df["Description"].str.contains("Estimated Luxury Tax Payroll", na=False)
    ]
    if total_row.empty:
        return None

    return {
        "team": team,
        "season": season,
        "luxury_tax_payroll_estimate": parse_dollars(total_row.iloc[0][season]),
        "source_file": path.name,
    }


# --- Main ---
def main(input_dir: Path, output_dir: Path) -> None:
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input path is not a directory: {input_dir}")

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        raise RuntimeError(f"Failed to create output directory: {output_dir}") from exc

    files = sorted(input_dir.rglob("*.xlsx"))
    if not files:
        print(f"No .xlsx files found in {input_dir}.")
        return

    print(f"Found {len(files)} .xlsx file(s).\n")

    all_players, all_payments, all_summaries = [], [], []

    for path in files:
        team, season = extract_team_season(path)
        print(f"Parsing {path.name} -> team={team}, season={season}...")

        players = parse_players(path, team, season)
        payments = parse_other_payments(path, team, season)
        summary = parse_summary(path, team, season)

        if not players.empty:
            all_players.append(players)
        if not payments.empty:
            all_payments.append(payments)
        if summary:
            all_summaries.append(summary)

    if all_players:
        df = pd.concat(all_players, ignore_index=True)
        out = output_dir / "players.parquet"
        try:
            df.to_parquet(out, index=False)
        except Exception as exc:
            raise RuntimeError(f"Failed to write players parquet to {out}.") from exc
        print(f"\nWrote {len(df)} player row(s) to {out}.")

    if all_payments:
        df = pd.concat(all_payments, ignore_index=True)
        out = output_dir / "other_payments.parquet"
        try:
            df.to_parquet(out, index=False)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to write other_payments parquet to {out}."
            ) from exc
        print(f"Wrote {len(df)} payment row(s) to {out}.")

    if all_summaries:
        df = pd.DataFrame(all_summaries)
        out = output_dir / "summary.parquet"
        try:
            df.to_parquet(out, index=False)
        except Exception as exc:
            raise RuntimeError(f"Failed to write summary parquet to {out}.") from exc
        print(f"Wrote {len(df)} summary row(s) to {out}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Parse Fangraphs payroll xlsx → parquet"
    )
    parser.add_argument(
        "--input", type=Path, default=DATA_DIR, help="Directory containing .xlsx files"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DIR,
        help="Directory to write parquet files",
    )
    args = parser.parse_args()

    main(args.input, args.output)
