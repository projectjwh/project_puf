-- int_nursing_home_staffing: Daily PBJ staffing → quarterly aggregation
-- Grain: CCN × quarter
-- Value added: Daily hours → quarterly averages, RN ratio calculation

{{ config(
    materialized='table',
    tags=['postacute', 'quality'],
) }}

with pbj_daily as (
    select
        ccn,
        work_date,
        data_year,
        extract(quarter from work_date::date) as quarter,
        cna_hours,
        lpn_hours,
        rn_hours,
        total_nurse_hours,
        physical_therapist_hours
    from {{ source('staging', 'stg_cms__pbj_staffing') }}
    where data_year between {{ var('min_data_year') }} and {{ var('max_data_year') }}
)

select
    ccn,
    data_year,
    quarter::int as quarter,
    count(*) as days_reported,
    round(avg(cna_hours), 2) as avg_daily_cna_hours,
    round(avg(lpn_hours), 2) as avg_daily_lpn_hours,
    round(avg(rn_hours), 2) as avg_daily_rn_hours,
    round(avg(total_nurse_hours), 2) as avg_daily_total_hours,
    round(avg(physical_therapist_hours), 2) as avg_daily_pt_hours,
    round(sum(rn_hours), 2) as total_quarterly_rn_hours,
    round(sum(total_nurse_hours), 2) as total_quarterly_nurse_hours,
    -- RN ratio: RN hours / total nurse hours
    case
        when sum(total_nurse_hours) > 0
        then round(sum(rn_hours)::numeric / sum(total_nurse_hours), 4)
    end as rn_ratio
from pbj_daily
group by ccn, data_year, quarter::int
