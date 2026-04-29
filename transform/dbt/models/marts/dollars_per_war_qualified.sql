-- Filters dollars_per_war to players with meaningful playing time.
-- Removes injury-shortened seasons which skew $/WAR extremes.
-- Thresholds: 100 PA for batters, 30 IP for pitchers.
-- Compare to dollars_per_war for full picture including injury seasons.

select *
from {{ ref('dollars_per_war') }}
where
    (player_type = 'batter'  and pa  >= 100)
    or (player_type = 'pitcher' and ip  >= 30)
    or player_type = 'two_way'