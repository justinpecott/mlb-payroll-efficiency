import textwrap

import streamlit as st

st.set_page_config(page_title="Definitions", page_icon="📖", layout="wide")

st.title("📖 Definitions & Methodology")
st.caption("A guide to the metrics and methods used in this analysis")


def md(text: str) -> None:
    """Render markdown with consistent spacing."""
    st.markdown(textwrap.dedent(text).strip())


st.header("Data Sources")
md(
    """
    **Payroll Data** — [Fangraphs](https://www.fangraphs.com) team payroll pages, manually downloaded
    for all 30 MLB teams across the 2021–2025 seasons. Includes guaranteed contracts, arbitration
    salaries, pre-arbitration salaries, and players no longer on the 40-man roster.

    **Batting & Pitching Stats** — Fangraphs leaderboards pulled via
    [pybaseball](https://github.com/jldbc/pybaseball), covering all players with at least 1 PA or 1 IP
    in each season.
    """
)

st.divider()

st.header("Key Metrics")

st.subheader("WAR — Wins Above Replacement")
md(
    """
    WAR measures a player's total contribution to their team compared to a freely available
    replacement-level player. A WAR of 0 means the player performed at replacement level —
    the equivalent of a typical minor league callup or waiver wire pickup.

    WAR is a **counting stat** — it accumulates over playing time. A player who plays
    162 games will generally accumulate more WAR than an equally skilled player who plays 81 games.
    This is an important consideration when comparing players across seasons — injury-shortened
    seasons will naturally produce lower WAR totals.

    **Fangraphs WAR tiers:**
    """
)

tiers = [
    ("MVP Level", "6.0+", "Elite season, MVP candidate"),
    ("Superstar", "5.0–6.0", "All-Star caliber, impact player"),
    ("All-Star", "4.0–5.0", "Clear above average, All-Star consideration"),
    ("Good Player", "3.0–4.0", "Solid regular, above average contributor"),
    ("Solid Starter", "2.0–3.0", "Average to slightly above average starter"),
    ("Role Player", "1.0–2.0", "Below average starter or valuable bench piece"),
    ("Scrub", "0.0–1.0", "Replacement level, borderline roster player"),
    ("Replacement or Worse", "< 0.0", "Below replacement level"),
]

col_tier, col_range, col_desc = st.columns([2, 1, 3])
col_tier.markdown("**Tier**")
col_range.markdown("**WAR Range**")
col_desc.markdown("**Description**")

for tier, war_range, description in tiers:
    c1, c2, c3 = st.columns([2, 1, 3])
    c1.markdown(f"**{tier}**")
    c2.markdown(war_range)
    c3.markdown(description)

st.divider()

st.subheader("\\$/WAR — Dollars per Win Above Replacement")
md(
    """
    \\$/WAR divides a player's salary by their total WAR to measure how much a team paid
    for each win of production. Lower is better — a player generating 5 WAR on a \\$1M
    salary is far more valuable than a player generating 5 WAR on a \\$30M salary.

    \\$/WAR is **NULL** for players with zero or negative WAR — dividing by zero or negative
    production doesn't produce a meaningful number.

    **Two versions are available:**
    - **Salary \\$/WAR** — uses the actual salary paid in that season
    - **AAV \\$/WAR** — uses the average annual value of the contract, better for evaluating
      long-term contract decisions
    """
)

st.subheader("Value Above Market")
md(
    """
    **Value Above Market** measures how much value a player generated relative to what they were paid,
    expressed in dollars.

    **Formula:** (League Average \\$/WAR × Player WAR) - Salary

    - **Positive** — the team paid less than market rate for the WAR generated. A player worth \\$20M
      on the open market but paid \\$1M generates +\\$19M in value above market.
    - **Negative** — the team overpaid relative to the production received. A player paid \\$35M who
      generates 0.1 WAR is deeply underwater.
    - Players with negative WAR produce negative value above market — they not only failed to
      generate wins but cost real salary dollars in the process.

    The league average \\$/WAR is calculated fresh each season, so a player's value above market
    is always relative to that year's market rate rather than a fixed benchmark.
    """
)

st.subheader("WAR per 600 PA / WAR per 180 IP")
md(
    """
    Rate-based WAR metrics that project a player's production over a full season of playing time.

    - **WAR per 600 PA** — standard full season for a position player
    - **WAR per 180 IP** — roughly a full season for a starting pitcher

    These are useful for **player evaluation** — understanding how good a player is regardless
    of how much they played. However they can overstate value for:
    - Platoon players who only face favorable matchups
    - Closers pitching in high-leverage situations
    - Players with small samples due to injury

    For **contract value analysis**, total WAR is the more appropriate metric — teams pay
    for the wins they actually receive, not projected wins.
    """
)

st.divider()

st.header("Contract Status")
md(
    """
    Fangraphs categorizes players into four contract status buckets:

    - **Guaranteed** — players with multi-year contracts or signed to guaranteed deals
    - **Eligible For Arb** — players with 3+ years of service time eligible for salary arbitration
    - **Not Yet Eligible For Arb** — players with less than 3 years of service time,
      typically earning near the league minimum
    - **No Longer On 40-Man Roster** — players who were paid but are no longer on the active roster,
      includes buyouts and salary dumps from trades

    Pre-arbitration players (Not Yet Eligible) represent the greatest value opportunity in baseball —
    teams control these players for 6 years at well below market rate, which is why young, talented
    rosters like the 2022 Orioles or 2021 Rays consistently top the efficiency rankings.
    """
)

st.divider()

st.header("Methodology Notes")
md(
    """
    - **Qualified players** — the main analysis uses a minimum playing time threshold of
      100 PA for batters and 30 IP for pitchers to filter out injury-shortened seasons that
      skew $/WAR extremes. The full dataset including all players is also available.
    - **Traded players** — players traded mid-season appear twice in the data, once for each team.
      Their WAR and salary are split by team as reported by Fangraphs.
    - **Two-way players** — Shohei Ohtani and others with both batting and pitching WAR have their
      total WAR summed across both contributions.
    - **Season range** — this analysis covers 2021–2025, starting post-COVID to avoid the
      distortions of the 2020 60-game season.
    - **Data pipeline** — payroll data was parsed from Fangraphs Excel exports, stats were
      pulled via pybaseball, both stored in Snowflake and transformed using dbt.
    """
)

st.divider()
st.caption(
    "Data sourced from Fangraphs via pybaseball · Pipeline built with Python, Snowflake, and dbt"
)
