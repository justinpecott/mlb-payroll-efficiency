with payroll as (

    select
        player_id,
        player_name,
        team,
        season,
        contract_status,
        salary,
        aav,
        age

    from {{ ref('stg_payroll_players') }}

    where salary is not null

),

batting as (

    select
        player_id,
        season,
        war        as batting_war,
        pa,
        wrc_plus,
        woba,
        def_runs

    from {{ ref('stg_batting') }}

),

pitching as (

    select
        player_id,
        season,
        war        as pitching_war,
        ip,
        era,
        fip,
        xfip,
        era_minus,
        fip_minus

    from {{ ref('stg_pitching') }}

),

joined as (

    select
        p.player_id,
        p.player_name,
        p.team,
        p.season,
        p.contract_status,
        p.salary,
        p.aav,
        p.age,

        -- WAR components
        coalesce(b.batting_war, 0)  as batting_war,
        coalesce(pt.pitching_war, 0) as pitching_war,
        coalesce(b.batting_war, 0) + coalesce(pt.pitching_war, 0) as total_war,

        -- batting context
        b.pa,
        b.wrc_plus,
        b.woba,
        b.def_runs,

        -- pitching context
        pt.ip,
        pt.era,
        pt.fip,
        pt.xfip,
        pt.era_minus,
        pt.fip_minus,

        -- player type flag
        case
            when b.player_id is not null and pt.player_id is not null then 'two_way'
            when b.player_id is not null then 'batter'
            when pt.player_id is not null then 'pitcher'
        end as player_type

    from payroll p
    left join batting b
        on p.player_id = b.player_id
        and p.season = b.season
    left join pitching pt
        on p.player_id = pt.player_id
        and p.season = pt.season

),

league_avg as (

    select
        season,
        avg(case when total_war > 0 then salary / total_war end) as avg_dollars_per_war
    from joined
    group by season

),

final as (

    select
        j.*,
        l.avg_dollars_per_war as league_avg_dollars_per_war,

        case
            when total_war < 0  then 'replacement_or_worse'
            when total_war < 1  then 'scrub'
            when total_war < 2  then 'role_player'
            when total_war < 3  then 'solid_starter'
            when total_war < 4  then 'good_player'
            when total_war < 5  then 'all_star'
            when total_war < 6  then 'superstar'
            when total_war >= 6 then 'mvp_level'
        end as war_tier,

        case
            when j.total_war > 0
            then (l.avg_dollars_per_war * j.total_war) - j.salary
        end as value_above_market,

        case
            when total_war > 0
            then salary / total_war
        end as dollars_per_war,

        case
            when total_war > 0
            then aav / total_war
        end as aav_per_war,

        case
            when pa > 0 then (total_war / pa) * 600
        end as war_per_600_pa,

        case
            when ip > 0 then (total_war / ip) * 180
        end as war_per_180_ip

    from joined j
    left join league_avg l
        on j.season = l.season

)

select * from final