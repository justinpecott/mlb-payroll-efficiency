with player_seasons as (

    select
        player_id,
        player_name,
        team,
        season,
        age,
        player_type,
        salary
    from {{ ref('dollars_per_war') }}
    where player_id is not null

),

player_span as (

    select
        player_id,
        min(season) as first_season,
        max(season) as last_season,
        max(age) as current_age
    from player_seasons
    group by player_id

),

latest_player_record as (

    select
        player_id,
        player_name,
        player_type,
        row_number() over (
            partition by player_id
            order by
                season desc,
                case
                    when player_type = 'two_way' then 3
                    when player_type = 'pitcher' then 2
                    when player_type = 'batter' then 1
                    else 0
                end desc,
                coalesce(salary, 0) desc,
                team asc,
                player_name asc
        ) as rn
    from player_seasons

)

select
    s.player_id,
    l.player_name,
    s.current_age,
    s.first_season,
    s.last_season,
    l.player_type
from player_span s
join latest_player_record l
    on s.player_id = l.player_id
   and l.rn = 1
