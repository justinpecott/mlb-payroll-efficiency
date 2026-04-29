-- Fails if dim_teams does not contain exactly 30 rows.
select *
from (
    select count(*) as row_count
    from {{ ref('dim_teams') }}
) t
where row_count != 30
