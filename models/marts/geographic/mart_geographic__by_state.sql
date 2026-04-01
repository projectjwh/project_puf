-- mart_geographic__by_state: State summary with provider counts and spending
-- Grain: state_fips × data_year
-- Lightweight state-level summary for dropdowns, maps, and quick lookups

{{ config(
    materialized='table',
    tags=['geographic', 'mart', 'api'],
    indexes=[
        {'columns': ['state_fips', 'data_year'], 'unique': true},
        {'columns': ['state_abbreviation']},
    ],
) }}

with benchmarks as (
    select * from {{ ref('int_geographic_benchmarks') }}
),

provider_stats as (
    select
        provider_state_fips as state_fips,
        data_year,
        count(distinct rendering_npi) as total_providers,
        sum(total_services) as total_services,
        sum(total_beneficiaries) as total_beneficiaries_served,
        sum(total_medicare_payments) as total_medicare_payments
    from {{ ref('int_provider_services') }}
    where provider_state_fips is not null
    group by provider_state_fips, data_year
),

prescriber_stats as (
    select
        prescriber_state_fips as state_fips,
        data_year,
        count(distinct prescriber_npi) as total_prescribers,
        sum(total_claims) as total_rx_claims,
        sum(total_drug_cost) as total_drug_cost,
        avg(generic_rate_pct) as avg_generic_rate,
        count(distinct case when has_opioid_prescriptions then prescriber_npi end) as opioid_prescribers
    from {{ ref('int_provider_prescriptions') }}
    where prescriber_state_fips is not null
    group by prescriber_state_fips, data_year
)

select
    b.state_fips,
    b.state_name,
    b.state_abbreviation,
    b.census_region,
    b.census_division,
    b.data_year,

    -- Beneficiaries
    b.total_beneficiaries,
    b.ma_participation_rate,

    -- Spending
    b.actual_per_capita_costs,
    b.standardized_per_capita_costs,
    b.spending_index,

    -- Provider supply
    coalesce(ps.total_providers, 0) as total_providers,
    coalesce(ps.total_services, 0) as total_services,
    coalesce(ps.total_medicare_payments, 0) as total_medicare_payments,

    -- Prescribing
    coalesce(rx.total_prescribers, 0) as total_prescribers,
    coalesce(rx.total_rx_claims, 0) as total_rx_claims,
    coalesce(rx.total_drug_cost, 0) as total_drug_cost,
    rx.avg_generic_rate,
    coalesce(rx.opioid_prescribers, 0) as opioid_prescribers

from benchmarks b
left join provider_stats ps on b.state_fips = ps.state_fips and b.data_year = ps.data_year
left join prescriber_stats rx on b.state_fips = rx.state_fips and b.data_year = rx.data_year
