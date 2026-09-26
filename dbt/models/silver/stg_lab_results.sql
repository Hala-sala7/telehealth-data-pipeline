-- Clean lab results + add normal range and a low / normal / high flag

with source as (
    select * from {{ source('bronze', 'lab_results') }}
),

ranges as (
    select
        test_name,
        try_cast(normal_low as double) as normal_low,
        try_cast(normal_high as double) as normal_high
    from {{ source('bronze', 'lab_reference_ranges') }}
),

cleaned as (
    select
        trim(result_id) as result_id,
        trim(patient_id) as patient_id,
        trim(test_name) as test_name,
        try_cast(result_value as double) as result_value,  -- 'N/A', 'error' -> null
        trim(unit) as unit,
        try_cast(collected_at as timestamp) as collected_at
    from source
)

select
    c.*,
    r.normal_low,
    r.normal_high,
    case
        when c.result_value < r.normal_low then 'low'
        when c.result_value > r.normal_high then 'high'
        else 'normal'
    end as result_flag
from cleaned c
left join ranges r using (test_name)
where c.result_value is not null  -- can not analyse text values
