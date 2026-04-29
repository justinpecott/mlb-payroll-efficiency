import pandas as pd
import plotly.express as px
import streamlit as st
from viz_shared import (
    DEFAULT_SEASONS,
    MONEY_FORMATS,
    PLAYER_TYPE_LABELS,
    WAR_TIER_LABELS,
    get_connection,
    query_df,
    show_empty_state,
)


@st.cache_data(ttl=3600, show_spinner=False)
def load_value_data(_conn, season: int) -> pd.DataFrame:
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
            league_avg_dollars_per_war,
            value_above_market / 1e6 AS value_above_market_m
        FROM dollars_per_war
        WHERE season = %s
        ORDER BY value_above_market_m DESC NULLS LAST
        """,
        params=(int(season),),
    )


def apply_filters(
    df: pd.DataFrame,
    player_types: list[str],
    contract_statuses: list[str],
    teams: list[str],
) -> pd.DataFrame:
    filtered = df.copy()

    if player_types:
        filtered = filtered[filtered["player_type_label"].isin(player_types)]
    if contract_statuses:
        filtered = filtered[filtered["contract_status"].isin(contract_statuses)]
    if teams:
        filtered = filtered[filtered["team"].isin(teams)]

    return filtered


st.set_page_config(page_title="Value Analysis", page_icon="💰", layout="wide")

st.title("💰 Value Above Market")
st.caption("How much value did each player generate relative to their salary?")
st.markdown(
    """
**Value Above Market** = (League Avg $/WAR × Player WAR) - Salary

Positive = team got a bargain · Negative = team overpaid
"""
)

conn = get_connection()

# --- Sidebar ---
st.sidebar.header("Filters")
season = st.sidebar.selectbox("Season", DEFAULT_SEASONS)

df = load_value_data(conn, season)
if show_empty_state(df, "No value analysis data found for this season."):
    st.stop()

df["war_tier_label"] = df["war_tier"].map(WAR_TIER_LABELS).fillna(df["war_tier"])
df["player_type_label"] = (
    df["player_type"].map(PLAYER_TYPE_LABELS).fillna(df["player_type"])
)

selected_player_types = st.sidebar.multiselect(
    "Player Type",
    options=["Batter", "Pitcher", "Two-Way"],
    default=["Batter", "Pitcher", "Two-Way"],
)

selected_contract_status = st.sidebar.multiselect(
    "Contract Status",
    options=sorted(df["contract_status"].dropna().unique().tolist()),
    default=sorted(df["contract_status"].dropna().unique().tolist()),
)

selected_teams = st.sidebar.multiselect(
    "Team",
    options=sorted(df["team"].dropna().unique().tolist()),
    default=[],
)

filtered = apply_filters(
    df=df,
    player_types=selected_player_types,
    contract_statuses=selected_contract_status,
    teams=selected_teams,
)

if show_empty_state(
    filtered,
    "No players match the current filters. Try broadening your selections.",
):
    st.stop()

# --- Summary metrics ---
valid_value = filtered[filtered["value_above_market_m"].notna()].copy()
league_avg = filtered["league_avg_dollars_per_war"].dropna()

col1, col2, col3 = st.columns(3)

if valid_value.empty:
    col1.metric("Biggest Bargain", "—", "No calculable values")
    col2.metric("Biggest Overpay", "—", "No calculable values")
else:
    biggest_bargain = valid_value.nlargest(1, "value_above_market_m").iloc[0]
    biggest_overpay = valid_value.nsmallest(1, "value_above_market_m").iloc[0]

    col1.metric(
        "Biggest Bargain",
        biggest_bargain["player_name"],
        f"${biggest_bargain['value_above_market_m']:.1f}M above market",
        delta_color="normal",
    )
    col2.metric(
        "Biggest Overpay",
        biggest_overpay["player_name"],
        f"${abs(biggest_overpay['value_above_market_m']):.1f}M below market",
        delta_color="inverse",
    )

if league_avg.empty:
    col3.metric("League Avg $/WAR", "—")
else:
    col3.metric("League Avg $/WAR", f"${league_avg.iloc[0] / 1e6:.1f}M")

st.divider()

# --- Bar chart: top bargains and overpays ---
top_n = st.slider("Show top/bottom N players", min_value=5, max_value=30, value=15)

if valid_value.empty:
    st.info("No non-null Value Above Market rows are available for charting.")
else:
    top = valid_value.nlargest(top_n, "value_above_market_m")
    bottom = valid_value.nsmallest(top_n, "value_above_market_m")
    chart_df = (
        pd.concat([top, bottom]).drop_duplicates().sort_values("value_above_market_m")
    )

    fig = px.bar(
        chart_df,
        x="value_above_market_m",
        y="player_name",
        color="value_above_market_m",
        color_continuous_scale=["#e63946", "#ffffff", "#52b788"],
        color_continuous_midpoint=0,
        orientation="h",
        hover_data={
            "team": True,
            "salary_m": ":.1f",
            "total_war": ":.1f",
            "contract_status": True,
            "war_tier_label": True,
        },
        labels={
            "value_above_market_m": "Value Above Market ($M)",
            "player_name": "",
        },
        title=f"{season} — Top {top_n} Bargains and Overpays",
        height=max(500, top_n * 2 * 25),
    )
    fig.add_vline(x=0, line_color="gray", line_width=1)
    fig.update_coloraxes(showscale=False)
    fig.update_layout(margin=dict(l=150))

    st.plotly_chart(fig, use_container_width=True)

# --- Table ---
st.subheader("Full Rankings")

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
        "value_above_market_m",
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
        "value_above_market_m": "Value Above Market",
    }
)

display = display.sort_values("Value Above Market", ascending=False, na_position="last")

st.dataframe(
    display.style.format(
        {
            **MONEY_FORMATS,
            "WAR": "{:.1f}",
        },
        na_rep="—",
    ),
    use_container_width=True,
    hide_index=True,
    height=600,
)
