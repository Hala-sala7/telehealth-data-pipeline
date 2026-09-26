-- percentages must be between 0 and 100
select month, no_show_rate_pct as rate
from {{ ref('agg_monthly_appointments') }}
where no_show_rate_pct not between 0 and 100

union all

select month, abnormal_rate_pct as rate
from {{ ref('agg_lab_results_by_test') }}
where abnormal_rate_pct not between 0 and 100
