-- mart_postacute__snf_quality: SNF quality dashboard
-- Grain: CCN
-- Cross-source: Five-Star + PBJ staffing

{{ config(
    materialized='table',
    tags=['postacute', 'quality'],
) }}

select
    ccn,
    facility_name,
    provider_state,
    overall_rating,
    health_inspection_rating,
    quality_rating,
    staffing_rating,
    rn_staffing_rating,
    total_number_of_penalties,
    total_fine_amount,
    abuse_icon,
    actual_avg_daily_rn_hours,
    actual_avg_daily_total_hours,
    actual_rn_ratio,
    staffing_consistency_flag,
    snapshot_date
from {{ ref('int_nursing_home_quality') }}
