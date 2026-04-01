-- int_ma_market: County-level MA penetration and enrollment trends
-- Grain: county_fips × data_year
-- Value added: Monthly enrollment → annual average, penetration rate computation

{{ config(
    materialized='table',
    tags=['medicare_advantage'],
) }}

with enrollment as (
    select
        county_fips,
        state_fips,
        state,
        data_year,
        enrollment_count,
        eligible_count,
        penetration_rate
    from {{ source('staging', 'stg_cms__ma_enrollment') }}
    where data_year between {{ var('min_data_year') }} and {{ var('max_data_year') }}
),

benchmarks as (
    select
        county_fips,
        year,
        ffs_per_capita,
        ma_benchmark,
        risk_score,
        quality_bonus_pct
    from {{ source('reference_tier2', 'ref_ma_benchmarks') }}
),

state_fips as (
    select state_fips, state_name
    from {{ source('reference', 'ref_state_fips') }}
)

select
    e.county_fips,
    e.state_fips,
    sf.state_name,
    e.data_year,
    sum(e.enrollment_count) as total_enrollment,
    avg(e.eligible_count) as avg_monthly_eligible,
    avg(e.penetration_rate) as avg_penetration_rate,
    count(distinct e.state) as months_reported,
    b.ffs_per_capita,
    b.ma_benchmark,
    b.risk_score,
    b.quality_bonus_pct,
    -- Benchmark-to-FFS ratio
    case
        when b.ffs_per_capita > 0
        then round(b.ma_benchmark::numeric / b.ffs_per_capita, 4)
    end as benchmark_to_ffs_ratio
from enrollment e
left join benchmarks b on e.county_fips = b.county_fips and e.data_year = b.year
left join state_fips sf on e.state_fips = sf.state_fips
group by e.county_fips, e.state_fips, sf.state_name, e.data_year,
         b.ffs_per_capita, b.ma_benchmark, b.risk_score, b.quality_bonus_pct
