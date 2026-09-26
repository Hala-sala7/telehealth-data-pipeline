-- Clean appointments table: one row per appointment, only for patients we know

with source as (
    select * from {{ source('bronze', 'appointments') }}
),

cleaned as (
    select
        trim(appointment_id) as appointment_id,
        trim(patient_id) as patient_id,
        trim(provider_name) as provider_name,
        trim(appointment_type) as appointment_type,
        try_cast(scheduled_at as timestamp) as scheduled_at,

        -- completed / Completed / Canceled / No Show ... -> 3 clean values
        case
            when lower(status) = 'completed' then 'completed'
            when lower(status) in ('cancelled', 'canceled') then 'cancelled'
            when lower(replace(status, ' ', '_')) = 'no_show' then 'no_show'
        end as status,

        -- empty or negative duration is wrong -> null
        case
            when try_cast(duration_minutes as integer) > 0 then try_cast(duration_minutes as integer)
        end as duration_minutes,

        try_cast(price_usd as decimal(10, 2)) as price_usd,
        _ingested_at
    from source
),

no_duplicates as (
    select *
    from cleaned
    qualify row_number() over (partition by appointment_id order by _ingested_at desc) = 1
)

-- inner join removes appointments for patients that do not exist
select a.*
from no_duplicates a
inner join {{ ref('stg_patients') }} p using (patient_id)
