-- Example business questions using the silver and gold layers
-- Run: duckdb data/warehouse.duckdb < queries/business_questions.sql

-- 1. Which providers have the most no-shows?
select
    provider_name,
    count(*) as appointments,
    round(100.0 * count(*) filter (where status = 'no_show') / count(*), 1) as no_show_rate_pct
from silver.stg_appointments
group by provider_name
order by no_show_rate_pct desc;

-- 2. Revenue growth from month to month (using lag)
select
    month,
    revenue_usd,
    lag(revenue_usd) over (order by month) as prev_month_revenue,
    round(100.0 * (revenue_usd - lag(revenue_usd) over (order by month))
          / nullif(lag(revenue_usd) over (order by month), 0), 1) as growth_pct
from gold.agg_monthly_appointments
order by month;

-- 3. Top 3 patients by revenue in each state (using rank)
select *
from (
    select
        state,
        patient_id,
        lifetime_revenue_usd,
        rank() over (partition by state order by lifetime_revenue_usd desc) as rank_in_state
    from gold.dim_patients
)
where rank_in_state <= 3
order by state, rank_in_state;

-- 4. Abnormal lab results by test and age group
select
    l.test_name,
    d.age_group,
    count(*) as results,
    round(100.0 * count(*) filter (where l.result_flag <> 'normal') / count(*), 1) as abnormal_rate_pct
from silver.stg_lab_results l
join gold.dim_patients d using (patient_id)
group by 1, 2
order by 1, 2;
