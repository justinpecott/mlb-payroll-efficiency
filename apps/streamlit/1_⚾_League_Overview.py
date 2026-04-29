import pandas as pd
import plotly.express as px
import streamlit as st
from viz_shared import (
    BASEBALL_FORMATS,
    DEFAULT_SEASONS,
    MONEY_FORMATS,
    PLAYER_TYPE_LABELS,
    TEAM_LOGOS,
    WAR_TIER_COLORS,
    WAR_TIER_LABELS,
    get_connection,
    query_df,
    show_empty_state,
)


@st.cache_data(ttl=3600, show_spinner=False)
def load_team_data(_conn, season: int) -> pd.DataFrame:
    return query_df(
        _conn,
        """
        SELECT
            team,
            season,
            league,
            division,
            total_war,
            total_salary / 1e6 AS payroll_m,
            luxury_tax_payroll_estimate / 1e6 AS luxury_tax_m,
            war_per_million,
            dollars_per_war,
            efficiency_rank,
            total_war_rank,
            roster_size,
            guaranteed_contracts,
            arb_eligible,
            pre_arb,
            mvp_level_players,
            superstar_players,
            all_star_players,
            good_players
        FROM team_war_value
        WHERE season = %s
        ORDER BY total_war DESC
        """,
        params=(int(season),),
    )


@st.cache_data(ttl=3600, show_spinner=False)
def load_player_data(_conn, team: str, season: int) -> pd.DataFrame:
    return query_df(
        _conn,
        """
        SELECT
            player_name,
            contract_status,
            salary / 1e6 AS salary_m,
            total_war,
            war_tier,
            player_type,
            dollars_per_war,
            wrc_plus,
            era,
            fip
        FROM dollars_per_war
        WHERE team = %s
          AND season = %s
        ORDER BY total_war DESC
        """,
        params=(team, int(season)),
    )


def build_team_scatter(filtered_df: pd.DataFrame, season: int):
    fig = px.scatter(
        filtered_df,
        x="payroll_m",
        y="total_war",
        size="roster_size",
        color="war_per_million",
        color_continuous_scale="RdYlGn",
        hover_name="team",
        hover_data={
            "payroll_m": ":.1f",
            "total_war": ":.1f",
            "war_per_million": ":.2f",
            "efficiency_rank": True,
            "total_war_rank": True,
            "roster_size": False,
            "logo": False,
        },
        labels={
            "payroll_m": "Payroll ($M)",
            "total_war": "Total WAR",
            "war_per_million": "WAR/$1M",
        },
        title=f"{season} Payroll vs WAR — colored by efficiency (WAR per $1M)",
        height=550,
    )

    # Replace marker dots with team logos.
    for _, row in filtered_df.iterrows():
        logo = row.get("logo")
        if not logo:
            continue

        fig.add_layout_image(
            dict(
                source=logo,
                x=row["payroll_m"],
                y=row["total_war"],
                xref="x",
                yref="y",
                sizex=8,
                sizey=8,
                sizing="contain",
                xanchor="center",
                yanchor="middle",
                layer="above",
            )
        )

    fig.update_traces(marker=dict(opacity=0))
    fig.add_hline(
        y=filtered_df["total_war"].median(),
        line_dash="dash",
        line_color="gray",
        opacity=0.4,
        annotation_text="median WAR",
    )
    fig.add_vline(
        x=filtered_df["payroll_m"].median(),
        line_dash="dash",
        line_color="gray",
        opacity=0.4,
        annotation_text="median payroll",
    )
    return fig


def build_player_war_chart(player_df: pd.DataFrame, selected_team: str, season: int):
    fig = px.bar(
        player_df.sort_values("total_war", ascending=True),
        x="total_war",
        y="player_name",
        color="war_tier_label",
        color_discrete_map=WAR_TIER_COLORS,
        orientation="h",
        hover_data=["salary_m", "contract_status", "dollars_per_war"],
        labels={"total_war": "WAR", "player_name": ""},
        title=f"{selected_team} {season} — WAR contributors",
        height=500,
    )

    avg_war = player_df["total_war"].mean()
    fig.add_vline(
        x=avg_war,
        line_dash="dash",
        line_color="gray",
        opacity=0.6,
        annotation_text=f"team avg {avg_war:.1f}",
        annotation_position="top",
    )

    for war_val, label in [(2, "solid starter"), (4, "all-star"), (6, "MVP")]:
        fig.add_vline(
            x=war_val,
            line_dash="dot",
            line_color="gray",
            opacity=0.3,
            annotation_text=label,
            annotation_position="top",
        )

    fig.update_layout(
        height=max(500, len(player_df) * 25),
        margin=dict(l=150),
        legend_title_text="WAR Tier",
    )
    return fig


st.set_page_config(page_title="MLB $/WAR Dashboard", page_icon="⚾", layout="wide")
st.title("⚾ MLB Payroll Efficiency Dashboard")
st.caption("Fangraphs data 2021–2025 · $/WAR analysis")

conn = get_connection()

st.sidebar.header("Filters")
season = st.sidebar.selectbox("Season", DEFAULT_SEASONS)

st.header(f"{season} Team Payroll Efficiency")
team_df = load_team_data(conn, season)

if show_empty_state(team_df, "No team data found for this season."):
    st.stop()

team_df["logo"] = team_df["team"].map(TEAM_LOGOS)

# Sidebar filters from available data.
leagues = ["All"] + sorted(team_df["league"].dropna().unique().tolist())
league_filter = st.sidebar.selectbox("League", leagues)

if league_filter != "All":
    division_options = ["All"] + sorted(
        team_df.loc[team_df["league"] == league_filter, "division"]
        .dropna()
        .unique()
        .tolist()
    )
    division_filter = st.sidebar.selectbox("Division", division_options)
else:
    division_filter = "All"
    st.sidebar.selectbox("Division", ["All"], disabled=True)

filtered_df = team_df.copy()
if league_filter != "All":
    filtered_df = filtered_df[filtered_df["league"] == league_filter]
if division_filter != "All":
    filtered_df = filtered_df[filtered_df["division"] == division_filter]

if show_empty_state(
    filtered_df, "No teams match the selected league/division filters."
):
    st.stop()

col1, col2, col3 = st.columns(3)
col1.metric("Avg Payroll", f"${filtered_df['payroll_m'].mean():.0f}M")
col2.metric("Avg Team WAR", f"{filtered_df['total_war'].mean():.1f}")
col3.metric("Avg $/WAR", f"${filtered_df['dollars_per_war'].mean() / 1e6:.1f}M")

fig = build_team_scatter(filtered_df, season)

st.header("Team Drill-down")
event = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key="scatter")

filtered_teams = sorted([str(team) for team in filtered_df["team"].dropna().tolist()])
clicked_team = None

if event and event.get("selection") and event["selection"].get("points"):
    # point_index is from the plotted frame (filtered_df), not full team_df.
    point_index = event["selection"]["points"][0].get("point_index")
    if point_index is not None and 0 <= point_index < len(filtered_df):
        clicked_team = str(filtered_df.iloc[point_index]["team"])

if not filtered_teams:
    st.info("No team options are available for the selected filters.")
    st.stop()

default_index = 0
if clicked_team in filtered_teams:
    default_index = filtered_teams.index(clicked_team)

selected_team_option = st.selectbox(
    "**Select a Team**", options=filtered_teams, index=default_index
)
selected_team = (
    str(selected_team_option) if selected_team_option is not None else filtered_teams[0]
)

team_summary = filtered_df.loc[filtered_df["team"] == selected_team].iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Payroll", f"${team_summary['payroll_m']:.0f}M")
c2.metric("Total WAR", f"{team_summary['total_war']:.1f}")
c3.metric("WAR/$1M", f"{team_summary['war_per_million']:.2f}")
c4.metric("Efficiency Rank", f"#{int(team_summary['efficiency_rank'])}")

player_df = load_player_data(conn, selected_team, season)
if show_empty_state(
    player_df, f"No player data found for {selected_team} in {season}."
):
    st.stop()

player_df["war_tier_label"] = player_df["war_tier"].map(WAR_TIER_LABELS)
player_df["player_type_label"] = player_df["player_type"].map(PLAYER_TYPE_LABELS)

fig2 = build_player_war_chart(player_df, selected_team, season)
st.plotly_chart(fig2, use_container_width=True)

st.subheader("Key Players")
valid_dpw = player_df[player_df["dollars_per_war"].notna()]
c1, c2, c3 = st.columns(3)

if valid_dpw.empty:
    c1.metric("💰 Best Value", "—", "No positive-WAR $/WAR rows")
    c2.metric("💸 Worst Contract", "—", "No positive-WAR $/WAR rows")
else:
    best_value = valid_dpw.nsmallest(1, "dollars_per_war").iloc[0]
    worst_contract = valid_dpw.nlargest(1, "dollars_per_war").iloc[0]
    c1.metric(
        "💰 Best Value",
        best_value["player_name"],
        f"${best_value['dollars_per_war']:,.0f}/WAR",
        delta_color="off",
    )
    c2.metric(
        "💸 Worst Contract",
        worst_contract["player_name"],
        f"${worst_contract['dollars_per_war']:,.0f}/WAR",
        delta_color="off",
    )

highest_war = player_df.nlargest(1, "total_war").iloc[0]
c3.metric(
    "⭐ WAR Leader",
    highest_war["player_name"],
    f"{highest_war['total_war']:.1f} WAR",
    delta_color="off",
)

st.subheader("Full Roster")
player_display = player_df.drop(columns=["war_tier", "player_type"]).rename(
    columns={
        "player_name": "Player",
        "contract_status": "Contract Status",
        "salary_m": "Salary",
        "total_war": "WAR",
        "war_tier_label": "WAR Tier",
        "player_type_label": "Type",
        "dollars_per_war": "$/WAR",
        "wrc_plus": "wRC+",
        "era": "ERA",
        "fip": "FIP",
    }
)

st.dataframe(
    player_display.style.format(
        {**MONEY_FORMATS, **BASEBALL_FORMATS},
        na_rep="—",
    ),
    use_container_width=True,
    hide_index=True,
    height=(len(player_display) + 1) * 35 + 3,
)
