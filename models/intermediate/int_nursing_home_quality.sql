-- int_nursing_home_quality: Five-star ratings + staffing merge
-- Grain: CCN
-- Value added: Combines rating dimensions with actual staffing data

{{ config(
    materialized='table',
    tags=['postacute', 'quality'],
) }}

with five_star as (
    select * from {{ ref('stg_cms__five_star') }}
),

-- Get the most recent quarterly staffing
latest_staffing as (
    select
        ccn,
        avg_daily_rn_hours,
        avg_daily_total_hours,
        rn_ratio,
        row_number() over (partition by ccn order by data_year desc, quarter desc) as rn
    from {{ ref('int_nursing_home_staffing') }}
)

select
    fs.ccn,
    fs.facility_name,
    fs.provider_state,
    fs.overall_rating,
    fs.health_inspection_rating,
    fs.quality_rating,
    fs.staffing_rating,
    fs.rn_staffing_rating,
    fs.total_weighted_health_survey_score,
    fs.total_number_of_penalties,
    fs.total_fine_amount,
    fs.abuse_icon,
    fs.snapshot_date,
    ls.avg_daily_rn_hours as actual_avg_daily_rn_hours,
    ls.avg_daily_total_hours as actual_avg_daily_total_hours,
    ls.rn_ratio as actual_rn_ratio,
    -- Flag: staffing rating vs actual performance
    case
        when fs.staffing_rating >= 4 and ls.rn_ratio < 0.15 then 'POTENTIAL_OVERRATING'
        when fs.staffing_rating <= 2 and ls.rn_ratio > 0.25 then 'POTENTIAL_UNDERRATING'
        else 'CONSISTENT'
    end as staffing_consistency_flag
from five_star fs
left join latest_staffing ls on fs.ccn = ls.ccn and ls.rn = 1
