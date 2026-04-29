"""Shared utilities and constants for Streamlit viz pages."""

from __future__ import annotations

import os
from typing import Any, Iterable

import pandas as pd
import snowflake.connector
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

DEFAULT_SEASONS: list[int] = [2025, 2024, 2023, 2022, 2021]

WAR_TIER_LABELS: dict[str, str] = {
    "mvp_level": "MVP Level",
    "superstar": "Superstar",
    "all_star": "All-Star",
    "good_player": "Good Player",
    "solid_starter": "Solid Starter",
    "role_player": "Role Player",
    "scrub": "Scrub",
    "replacement_or_worse": "Replacement or Worse",
}

WAR_TIER_COLORS: dict[str, str] = {
    "MVP Level": "#1a472a",
    "Superstar": "#2d6a4f",
    "All-Star": "#52b788",
    "Good Player": "#95d5b2",
    "Solid Starter": "#b7e4c7",
    "Role Player": "#f4d35e",
    "Scrub": "#ee8959",
    "Replacement or Worse": "#e63946",
}

PLAYER_TYPE_LABELS: dict[str, str] = {
    "batter": "Batter",
    "pitcher": "Pitcher",
    "two_way": "Two-Way",
}

TEAM_LOGOS: dict[str, str] = {
    "Angels": "https://a.espncdn.com/i/teamlogos/mlb/500/laa.png",
    "Astros": "https://a.espncdn.com/i/teamlogos/mlb/500/hou.png",
    "Athletics": "https://a.espncdn.com/i/teamlogos/mlb/500/oak.png",
    "Blue Jays": "https://a.espncdn.com/i/teamlogos/mlb/500/tor.png",
    "Braves": "https://a.espncdn.com/i/teamlogos/mlb/500/atl.png",
    "Brewers": "https://a.espncdn.com/i/teamlogos/mlb/500/mil.png",
    "Cardinals": "https://a.espncdn.com/i/teamlogos/mlb/500/stl.png",
    "Cubs": "https://a.espncdn.com/i/teamlogos/mlb/500/chc.png",
    "Diamondbacks": "https://a.espncdn.com/i/teamlogos/mlb/500/ari.png",
    "Dodgers": "https://a.espncdn.com/i/teamlogos/mlb/500/lad.png",
    "Giants": "https://a.espncdn.com/i/teamlogos/mlb/500/sf.png",
    "Guardians": "https://a.espncdn.com/i/teamlogos/mlb/500/cle.png",
    "Mariners": "https://a.espncdn.com/i/teamlogos/mlb/500/sea.png",
    "Marlins": "https://a.espncdn.com/i/teamlogos/mlb/500/mia.png",
    "Mets": "https://a.espncdn.com/i/teamlogos/mlb/500/nym.png",
    "Nationals": "https://a.espncdn.com/i/teamlogos/mlb/500/wsh.png",
    "Orioles": "https://a.espncdn.com/i/teamlogos/mlb/500/bal.png",
    "Padres": "https://a.espncdn.com/i/teamlogos/mlb/500/sd.png",
    "Phillies": "https://a.espncdn.com/i/teamlogos/mlb/500/phi.png",
    "Pirates": "https://a.espncdn.com/i/teamlogos/mlb/500/pit.png",
    "Rangers": "https://a.espncdn.com/i/teamlogos/mlb/500/tex.png",
    "Rays": "https://a.espncdn.com/i/teamlogos/mlb/500/tb.png",
    "Red Sox": "https://a.espncdn.com/i/teamlogos/mlb/500/bos.png",
    "Reds": "https://a.espncdn.com/i/teamlogos/mlb/500/cin.png",
    "Rockies": "https://a.espncdn.com/i/teamlogos/mlb/500/col.png",
    "Royals": "https://a.espncdn.com/i/teamlogos/mlb/500/kc.png",
    "Tigers": "https://a.espncdn.com/i/teamlogos/mlb/500/det.png",
    "Twins": "https://a.espncdn.com/i/teamlogos/mlb/500/min.png",
    "White Sox": "https://a.espncdn.com/i/teamlogos/mlb/500/chw.png",
    "Yankees": "https://a.espncdn.com/i/teamlogos/mlb/500/nyy.png",
}

MONEY_FORMATS: dict[str, str] = {
    "Salary": "${:.2f}M",
    "$/WAR": "${:,.0f}",
    "Value Above Market": "${:.1f}M",
}

BASEBALL_FORMATS: dict[str, str] = {
    "WAR": "{:.1f}",
    "wRC+": "{:.0f}",
    "ERA": "{:.2f}",
    "FIP": "{:.2f}",
}


def _required_env_vars() -> tuple[str, ...]:
    return (
        "SNOWFLAKE_ACCOUNT",
        "SNOWFLAKE_USER",
        "SNOWFLAKE_PASSWORD",
        "SNOWFLAKE_WAREHOUSE",
        "SNOWFLAKE_DATABASE",
    )


def _missing_env_vars() -> list[str]:
    return [key for key in _required_env_vars() if not os.getenv(key)]


@st.cache_resource(show_spinner=False)
def get_connection() -> snowflake.connector.SnowflakeConnection:
    """Return a cached Snowflake connection for Streamlit sessions."""
    missing = _missing_env_vars()
    if missing:
        raise RuntimeError(
            f"Missing required Snowflake environment variables: {', '.join(missing)}"
        )

    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA", "ANALYTICS"),
    )


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [str(c).lower() for c in df.columns]
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def query_df(
    _conn: snowflake.connector.SnowflakeConnection,
    sql: str,
    params: Iterable[Any] | None = None,
) -> pd.DataFrame:
    """
    Execute a SQL query and return a DataFrame with lowercase column names.

    Prefer positional parameters in SQL (`%s`) and pass values via `params`.
    """
    with _conn.cursor() as cur:
        cur.execute(sql, tuple(params) if params is not None else None)
        df = cur.fetch_pandas_all()
    return _normalize_columns(df)


def safe_selected_seasons(
    available_seasons: Iterable[int], default: list[int] | None = None
) -> list[int]:
    """Return a stable descending list of selected seasons."""
    seasons = sorted({int(s) for s in available_seasons}, reverse=True)
    if not seasons:
        return []
    if default is None:
        return seasons
    selected = [s for s in default if s in seasons]
    return selected or seasons


def show_empty_state(df: pd.DataFrame, message: str) -> bool:
    """
    Show a standard empty-state message and return True when empty.

    Usage:
        if show_empty_state(filtered_df, "No rows for selected filters."):
            st.stop()
    """
    if df.empty:
        st.info(message)
        return True
    return False
