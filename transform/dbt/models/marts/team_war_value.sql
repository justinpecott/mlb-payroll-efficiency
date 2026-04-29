with player_seasons as (

    select * from {{ ref('dollars_per_war_qualified') }}

),

payroll_summary as (

    select * from {{ ref('stg_payroll_summary') }}

),

team_aggregated as (

    select
        team,
        season,

        -- payroll
        sum(salary)                             as total_salary,

        -- WAR
        sum(total_war)                          as total_war,
        sum(batting_war)                        as total_batting_war,
        sum(pitching_war)                       as total_pitching_war,

        -- $/WAR
        case
            when sum(total_war) > 0
            then sum(salary) / sum(total_war)
        end                                     as dollars_per_war,

        -- roster composition
        count(*)                                as roster_size,
        count(case when player_type = 'batter'   then 1 end) as batters,
        count(case when player_type = 'pitcher'  then 1 end) as pitchers,
        count(case when player_type = 'two_way'  then 1 end) as two_way_players,

        -- contract status breakdown
        count(case when contract_status = 'Guaranteed'                  then 1 end) as guaranteed_contracts,
        count(case when contract_status = 'Eligible For Arb'            then 1 end) as arb_eligible,
        count(case when contract_status = 'Not Yet Eligible For Arb'    then 1 end) as pre_arb,

        -- WAR tier breakdown
        count(case when war_tier = 'mvp_level'          then 1 end) as mvp_level_players,
        count(case when war_tier = 'superstar'          then 1 end) as superstar_players,
        count(case when war_tier = 'all_star'           then 1 end) as all_star_players,
        count(case when war_tier = 'good_player'        then 1 end) as good_players,
        count(case when war_tier = 'solid_starter'      then 1 end) as solid_starters,
        count(case when war_tier = 'role_player'        then 1 end) as role_players,
        count(case when war_tier = 'scrub'              then 1 end) as scrubs,
        count(case when war_tier = 'replacement_or_worse' then 1 end) as replacement_or_worse

    from player_seasons
    group by team, season

),

final as (

    select
        t.*,
        s.luxury_tax_payroll_estimate,
        dt.team_id,
        dt.abbreviation,
        dt.league,
        dt.division,

        -- payroll efficiency: WAR generated per $1M spent
        case
            when t.total_salary > 0
            then t.total_war / (t.total_salary / 1000000)
        end                                     as war_per_million,

        -- luxury tax vs actual salary delta
        s.luxury_tax_payroll_estimate - t.total_salary as luxury_tax_vs_salary_delta,

        -- rank by total WAR within season (1 = most WAR)
        rank() over (
            partition by t.season
            order by t.total_war desc
        )                                       as total_war_rank,

        -- rank by efficiency within season (1 = most efficient)
        rank() over (
            partition by t.season
            order by
                case
                    when t.total_salary > 0
                    then t.total_war / (t.total_salary / 1000000)
                end desc nulls last
        )                                       as efficiency_rank

    from team_aggregated t
    left join payroll_summary s
        on t.team = s.team
        and t.season = s.season
    left join {{ ref('dim_teams') }} dt
        on t.team = dt.team_name

)

select * from final
order by season, dollars_per_war asc