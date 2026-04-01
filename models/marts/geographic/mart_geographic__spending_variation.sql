-- mart_geographic__spending_variation: State-level spending variation for Geographic Explorer
-- Grain: state_fips × data_year
-- Value added: pre-computed spending indices, MA context, service breakdown

{{ config(
    materialized='table',
    tags=['geographic', 'mart', 'api'],
    indexes=[
        {'columns': ['state_fips', 'data_year'], 'unique': true},
        {'columns': ['data_year']},
        {'columns': ['census_region']},
    ],
) }}

with benchmarks as (
    select * from {{ ref('int_geographic_benchmarks') }}
),

-- Provider counts per state per year (from Part B)
provider_counts as (
    select
        provider_state_fips as state_fips,
        data_year,
        count(distinct rendering_npi) as provider_count,
        sum(total_services) as state_total_services,
        sum(total_medicare_payments) as state_total_medicare_payments
    from {{ ref('int_provider_services') }}
    where provider_state_fips is not null
    group by provider_state_fips, data_year
)

select
    -- Geography
    b.state_fips,
    b.state_name,
    b.state_abbreviation,
    b.census_region,
    b.census_division,
    b.data_year,

    -- Beneficiary context
    b.total_beneficiaries,
    b.total_beneficiaries_ffs,
    b.total_beneficiaries_ma,
    b.ma_participation_rate,

    -- Spending
    b.actual_per_capita_costs,
    b.standardized_per_capita_costs,
    b.spending_index,
    b.standardized_spending_index,

    -- Service breakdown
    b.ip_per_capita_costs,
    b.op_per_capita_costs,
    b.snf_per_capita_costs,
    b.hha_per_capita_costs,
    b.hospice_per_capita_costs,
    b.partb_per_capita_costs,
    b.partd_per_capita_costs,
    b.dme_per_capita_costs,

    -- Utilization
    b.ip_covered_stays_per_1000,
    b.op_visits_per_1000,
    b.er_visits_per_1000,
    b.readmission_rate,

    -- National benchmarks
    b.national_per_capita_costs,
    b.national_standardized_per_capita,
    b.national_ma_rate,
    b.national_readmission_rate,

    -- MA penetration
    b.ma_penetration_index,

    -- Provider supply from Part B
    pc.provider_count,
    pc.state_total_services,
    pc.state_total_medicare_payments,

    -- Providers per 1000 beneficiaries
    case
        when b.total_beneficiaries > 0
        then round(pc.provider_count::numeric / b.total_beneficiaries * 1000, 2)
    end as providers_per_1000_benes

from benchmarks b
left join provider_counts pc on b.state_fips = pc.state_fips and b.data_year = pc.data_year
