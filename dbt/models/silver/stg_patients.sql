-- Clean patients table: one row per patient

with source as (
    select * from {{ source('bronze', 'patients') }}
),

cleaned as (
    select
        trim(patient_id) as patient_id,
        upper(left(trim(first_name), 1)) || lower(substr(trim(first_name), 2)) as first_name,
        upper(left(trim(last_name), 1)) || lower(substr(trim(last_name), 2)) as last_name,

        -- M, male, MALE, f, Female ... -> male / female / unknown
        case
            when lower(trim(gender)) in ('m', 'male') then 'male'
            when lower(trim(gender)) in ('f', 'female') then 'female'
            else 'unknown'
        end as gender,

        -- dates come in 3 different formats
        coalesce(
            try_strptime(date_of_birth, '%Y-%m-%d'),
            try_strptime(date_of_birth, '%d/%m/%Y'),
            try_strptime(date_of_birth, '%Y/%m/%d')
        )::date as date_of_birth,

        upper(trim(state)) as state,
        nullif(lower(trim(email)), '') as email,
        try_cast(signup_at as timestamp) as signup_at,
        _ingested_at
    from source
)

-- remove duplicates (keep the latest loaded row)
select *
from cleaned
qualify row_number() over (partition by patient_id order by _ingested_at desc) = 1
