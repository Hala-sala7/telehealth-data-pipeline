-- revenue should never be negative (the test fails if this returns any rows)
select *
from {{ ref('agg_monthly_appointments') }}
where revenue_usd < 0
