-- mart_ma__market_penetration: County MA enrollment share
-- Grain: county_fips × data_year

{{ config(
    materialized='table',
    tags=['medicare_advantage'],
) }}

select
    county_fips,
    state_fips,
    state_name,
    data_year,
    total_enrollment,
    avg_monthly_eligible,
    avg_penetration_rate,
    ffs_per_capita,
    ma_benchmark,
    risk_score,
    quality_bonus_pct,
    benchmark_to_ffs_ratio
from {{ ref('int_ma_market') }}
