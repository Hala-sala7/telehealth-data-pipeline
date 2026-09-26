-- One row per patient with age group and appointment numbers

with appointment_stats as (
    select
        patient_id,
        count(*) as total_appointments,
        count(*) filter (where status = 'completed') as completed_appointments,
        min(scheduled_at) as first_appointment_at,
        max(scheduled_at) as last_appointment_at,
        sum(price_usd) filter (where status = 'completed') as lifetime_revenue_usd
    from {{ ref('stg_appointments') }}
    group by patient_id
),

patients as (
    select
        *,
        date_diff('year', date_of_birth, current_date) as age
    from {{ ref('stg_patients') }}
)

select
    p.patient_id,
    p.first_name,
    p.last_name,
    p.gender,
    p.state,
    p.age,
    case
        when p.age < 30 then '18-29'
        when p.age < 45 then '30-44'
        when p.age < 60 then '45-59'
        else '60+'
    end as age_group,
    p.signup_at,
    coalesce(a.total_appointments, 0) as total_appointments,
    coalesce(a.completed_appointments, 0) as completed_appointments,
    a.first_appointment_at,
    a.last_appointment_at,
    coalesce(a.lifetime_revenue_usd, 0) as lifetime_revenue_usd
from patients p
left join appointment_stats a using (patient_id)
