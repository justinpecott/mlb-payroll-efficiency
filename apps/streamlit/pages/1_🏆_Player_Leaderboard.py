import pandas as pd
import streamlit as st
from viz_shared import (
    BASEBALL_FORMATS,
    MONEY_FORMATS,
    PLAYER_TYPE_LABELS,
    WAR_TIER_LABELS,
    get_connection,
    query_df,
    safe_selected_seasons,
    show_empty_state,
)


@st.cache_data(ttl=3600, show_spinner=False)
def load_player_leaderboard(_conn) -> pd.DataFrame:
    return query_df(
        _conn,
        """
        SELECT
            player_name,
            team,
            season,
            player_type,
            contract_status,
            salary / 1e6 AS salary_m,
            total_war,
            war_tier,
            dollars_per_war,
            war_per_600_pa,
            war_per_180_ip,
            wrc_plus,
            era,
            fip,
            pa,
            ip
        FROM dollars_per_war_qualified
        ORDER BY total_war DESC
        """,
    )


def apply_filters(
    df: pd.DataFrame,
    seasons: list[int],
    player_types: list[str],
    war_tiers: list[str],
    teams: list[str],
) -> pd.DataFrame:
    filtered = df.copy()

    if seasons:
        filtered = filtered[filtered["season"].isin(seasons)]
    if player_types:
        filtered = filtered[filtered["player_type_label"].isin(player_types)]
    if war_tiers:
        filtered = filtered[filtered["war_tier_label"].isin(war_tiers)]
    if teams:
        filtered = filtered[filtered["team"].isin(teams)]

    return filtered


st.set_page_config(page_title="Player Leaderboard", page_icon="⚾", layout="wide")
st.title("🏆 Player Leaderboard")
st.caption("Fangraphs data 2021–2025 · Qualified players only (100 PA / 30 IP)")

conn = get_connection()
df = load_player_leaderboard(conn)

if show_empty_state(df, "No player leaderboard data is currently available."):
    st.stop()

df["war_tier_label"] = df["war_tier"].map(WAR_TIER_LABELS).fillna(df["war_tier"])
df["player_type_label"] = (
    df["player_type"].map(PLAYER_TYPE_LABELS).fillna(df["player_type"])
)

# --- Sidebar Filters ---
st.sidebar.header("Filters")

available_seasons = sorted(
    df["season"].dropna().astype(int).unique().tolist(), reverse=True
)
selected_seasons = st.sidebar.multiselect(
    "Season",
    options=available_seasons,
    default=safe_selected_seasons(available_seasons),
)

selected_player_types = st.sidebar.multiselect(
    "Player Type",
    options=["Batter", "Pitcher", "Two-Way"],
    default=["Batter", "Pitcher", "Two-Way"],
)

selected_war_tiers = st.sidebar.multiselect(
    "WAR Tier",
    options=list(WAR_TIER_LABELS.values()),
    default=list(WAR_TIER_LABELS.values()),
)

selected_teams = st.sidebar.multiselect(
    "Team",
    options=sorted(df["team"].dropna().unique().tolist()),
    default=[],
)

# --- Sort ---
sort_col = st.selectbox(
    "**Sort by**",
    options=["WAR", "$/WAR", "Salary", "wRC+", "ERA", "FIP"],
    index=0,
)

sort_map = {
    "WAR": ("total_war", False),
    "$/WAR": ("dollars_per_war", True),
    "Salary": ("salary_m", False),
    "wRC+": ("wrc_plus", False),
    "ERA": ("era", True),
    "FIP": ("fip", True),
}

# --- Apply Filters ---
filtered = apply_filters(
    df=df,
    seasons=selected_seasons,
    player_types=selected_player_types,
    war_tiers=selected_war_tiers,
    teams=selected_teams,
)

if show_empty_state(
    filtered, "No players match the current filters. Try broadening your selections."
):
    st.stop()

sort_field, sort_asc = sort_map[sort_col]
filtered = filtered.sort_values(sort_field, ascending=sort_asc, na_position="last")

st.caption(f"{len(filtered)} players")

# --- Display ---
display = filtered[
    [
        "player_name",
        "team",
        "season",
        "player_type_label",
        "contract_status",
        "salary_m",
        "total_war",
        "war_tier_label",
        "dollars_per_war",
        "wrc_plus",
        "era",
        "fip",
    ]
].rename(
    columns={
        "player_name": "Player",
        "team": "Team",
        "season": "Season",
        "player_type_label": "Type",
        "contract_status": "Contract Status",
        "salary_m": "Salary",
        "total_war": "WAR",
        "war_tier_label": "WAR Tier",
        "dollars_per_war": "$/WAR",
        "wrc_plus": "wRC+",
        "era": "ERA",
        "fip": "FIP",
    }
)

st.dataframe(
    display.style.format(
        {
            **MONEY_FORMATS,
            **BASEBALL_FORMATS,
        },
        na_rep="—",
    ),
    use_container_width=True,
    hide_index=True,
    height=700,
)
