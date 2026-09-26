-- Lab results per test per month + how many were not normal

select
    test_name,
    unit,
    date_trunc('month', collected_at)::date as month,
    count(*) as total_results,
    round(avg(result_value), 2) as avg_value,
    count(*) filter (where result_flag = 'low') as low_results,
    count(*) filter (where result_flag = 'high') as high_results,
    round(100.0 * count(*) filter (where result_flag <> 'normal') / count(*), 1) as abnormal_rate_pct
from {{ ref('stg_lab_results') }}
group by 1, 2, 3
order by 1, 3
