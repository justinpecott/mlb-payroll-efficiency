with source as (

    select * from {{ source('raw', 'payroll_players') }}

),

renamed as (

    select
        -- ids
        player_id,
        player                   as player_name,
        team,
        season,

        -- contract details
        contract_status,
        contract,
        info                     as contract_notes,
        service_time::float      as service_time,
        age,

        -- financials
        salary,
        aav,
        future_salaries::variant as future_salaries,

        -- metadata
        source_file

    from source

)

select * from renamed
where coalesce(lower(trim(player_id)), '') not like 'sa%'
