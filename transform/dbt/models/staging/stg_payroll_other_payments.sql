with source as (

    select * from {{ source('raw', 'payroll_other_payments') }}

),

renamed as (

    select
        team,
        season,
        payment_type,
        description              as payment_description,
        amount,
        future_amounts::variant  as future_amounts,
        source_file

    from source

)

select * from renamed
