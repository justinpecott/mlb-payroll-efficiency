with source as (

    select * from {{ source('raw', 'payroll_summary') }}

),

renamed as (

    select
        team,
        season,
        luxury_tax_payroll_estimate,
        source_file

    from source

)

select * from renamed