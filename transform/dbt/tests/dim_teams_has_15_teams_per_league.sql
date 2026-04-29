-- Fails if dim_teams does not contain exactly 15 teams in each league (AL and NL).
with actual as (
    select
        league,
        count(*) as team_count
    from {{ ref('dim_teams') }}
    group by league
),

expected as (
    select 'AL' as league, 15 as expected_count
    union all
    select 'NL' as league, 15 as expected_count
),

mismatches as (
    -- Missing league or incorrect team count
    select
        e.league,
        coalesce(a.team_count, 0) as actual_count,
        e.expected_count
    from expected e
    left join actual a
        on a.league = e.league
    where coalesce(a.team_count, 0) != e.expected_count

    union all

    -- Unexpected extra leagues
    select
        a.league,
        a.team_count as actual_count,
        15 as expected_count
    from actual a
    left join expected e
        on e.league = a.league
    where e.league is null
)

select *
from mismatches
