-- Monthly numbers: appointments, no-show rate and revenue

select
    date_trunc('month', scheduled_at)::date as month,
    count(*) as total_appointments,
    count(*) filter (where status = 'completed') as completed,
    count(*) filter (where status = 'cancelled') as cancelled,
    count(*) filter (where status = 'no_show') as no_shows,
    round(100.0 * count(*) filter (where status = 'no_show') / count(*), 1) as no_show_rate_pct,
    coalesce(sum(price_usd) filter (where status = 'completed'), 0) as revenue_usd,
    count(distinct patient_id) as active_patients
from {{ ref('stg_appointments') }}
group by 1
order by 1
