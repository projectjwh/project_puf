-- int_geographic_benchmarks: Geographic spending and utilization benchmarks
-- Grain: state_fips × data_year (state-level rows from GeoVar)
-- Value added over staging:
--   - Filters to state-level geography (most useful for benchmarking)
--   - Adds national average for comparison
--   - Computes spending indices (state / national ratio)
--   - Joins state names from reference
--   - Provides MA penetration context

{{ config(
    materialized='table',
    tags=['intermediate', 'geographic'],
) }}

with state_data as (
    select * from {{ ref('stg_cms__geographic_variation') }}
    where bene_geo_lvl = 'State'
      and state_fips is not null
),

national_data as (
    select
        data_year,
        actual_per_capita_costs as national_per_capita_costs,
        standardized_per_capita_costs as national_standardized_per_capita,
        ma_participation_rate as national_ma_rate,
        readmission_rate as national_readmission_rate,
        total_beneficiaries as national_total_beneficiaries
    from {{ ref('stg_cms__geographic_variation') }}
    where bene_geo_lvl = 'National'
),

states as (
    select
        state_fips,
        state_name,
        state_abbreviation,
        region,
        division
    from {{ source('reference', 'ref_state_fips') }}
)

select
    -- Geography
    s.state_fips,
    st.state_name,
    st.state_abbreviation,
    st.region as census_region,
    st.division as census_division,
    s.bene_geo_desc as state_description,
    s.data_year,

    -- Beneficiary counts
    s.total_beneficiaries,
    s.total_beneficiaries_ffs,
    s.total_beneficiaries_ma,
    s.ma_participation_rate,

    -- Spending
    s.total_actual_costs,
    s.actual_per_capita_costs,
    s.standardized_per_capita_costs,

    -- Spending index (state / national)
    case
        when n.national_per_capita_costs > 0
        then round(s.actual_per_capita_costs::numeric / n.national_per_capita_costs, 4)
    end as spending_index,

    case
        when n.national_standardized_per_capita > 0
        then round(s.standardized_per_capita_costs::numeric / n.national_standardized_per_capita, 4)
    end as standardized_spending_index,

    -- Service category spending
    s.ip_per_capita_costs,
    s.op_per_capita_costs,
    s.snf_per_capita_costs,
    s.hha_per_capita_costs,
    s.hospice_per_capita_costs,
    s.partb_per_capita_costs,
    s.partd_per_capita_costs,
    s.dme_per_capita_costs,

    -- Utilization
    s.ip_covered_stays_per_1000,
    s.op_visits_per_1000,
    s.er_visits_per_1000,
    s.readmission_rate,

    -- National benchmarks for comparison
    n.national_per_capita_costs,
    n.national_standardized_per_capita,
    n.national_ma_rate,
    n.national_readmission_rate,

    -- MA penetration comparison
    case
        when n.national_ma_rate > 0
        then round(s.ma_participation_rate::numeric / n.national_ma_rate, 4)
    end as ma_penetration_index

from state_data s
left join national_data n on s.data_year = n.data_year
left join states st on s.state_fips = st.state_fips
