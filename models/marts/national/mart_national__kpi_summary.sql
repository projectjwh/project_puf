-- mart_national__kpi_summary: National-level KPIs for dashboard
-- Grain: one row per data_year
-- Value added: pre-aggregated national statistics with YOY change

{{ config(
    materialized='table',
    tags=['national', 'mart', 'api'],
    indexes=[
        {'columns': ['data_year'], 'unique': true},
    ],
) }}

with part_b_agg as (
    select
        data_year,
        count(distinct rendering_npi) as active_providers_partb,
        sum(total_services) as national_total_services,
        sum(total_beneficiaries) as national_total_beneficiaries,
        sum(total_medicare_payments) as national_total_medicare_payments,
        sum(total_medicare_standardized) as national_total_standardized_payments,
        avg(payment_per_beneficiary) as avg_payment_per_beneficiary,
        avg(unique_hcpcs_count) as avg_hcpcs_per_provider
    from {{ ref('int_provider_services') }}
    group by data_year
),

part_d_agg as (
    select
        data_year,
        count(distinct prescriber_npi) as active_prescribers,
        sum(total_claims) as national_total_rx_claims,
        sum(total_drug_cost) as national_total_drug_cost,
        avg(generic_rate_pct) as avg_generic_rate,
        sum(opioid_claims) as national_opioid_claims,
        avg(opioid_claim_rate_pct) as avg_opioid_rate,
        count(distinct case when has_opioid_prescriptions then prescriber_npi end) as opioid_prescribers,
        count(distinct case when is_high_opioid_prescriber then prescriber_npi end) as high_opioid_prescribers
    from {{ ref('int_provider_prescriptions') }}
    group by data_year
),

geo_national as (
    select
        data_year,
        total_beneficiaries as national_medicare_beneficiaries,
        actual_per_capita_costs as national_per_capita_costs,
        standardized_per_capita_costs as national_standardized_per_capita,
        ma_participation_rate as national_ma_rate,
        readmission_rate as national_readmission_rate
    from {{ ref('stg_cms__geographic_variation') }}
    where bene_geo_lvl = 'National'
)

select
    coalesce(b.data_year, d.data_year, g.data_year) as data_year,

    -- Provider counts
    b.active_providers_partb,
    d.active_prescribers,

    -- Part B KPIs
    b.national_total_services,
    b.national_total_beneficiaries,
    b.national_total_medicare_payments,
    b.national_total_standardized_payments,
    b.avg_payment_per_beneficiary,
    b.avg_hcpcs_per_provider,

    -- Part D KPIs
    d.national_total_rx_claims,
    d.national_total_drug_cost,
    d.avg_generic_rate,

    -- Opioid KPIs
    d.national_opioid_claims,
    d.avg_opioid_rate,
    d.opioid_prescribers,
    d.high_opioid_prescribers,

    -- GeoVar KPIs
    g.national_medicare_beneficiaries,
    g.national_per_capita_costs,
    g.national_standardized_per_capita,
    g.national_ma_rate,
    g.national_readmission_rate,

    -- YOY change (joined to prior year)
    round(
        (b.national_total_medicare_payments - lag(b.national_total_medicare_payments)
            over (order by b.data_year))::numeric
        / nullif(lag(b.national_total_medicare_payments) over (order by b.data_year), 0) * 100,
        2
    ) as yoy_payment_change_pct,

    round(
        (d.national_total_drug_cost - lag(d.national_total_drug_cost)
            over (order by d.data_year))::numeric
        / nullif(lag(d.national_total_drug_cost) over (order by d.data_year), 0) * 100,
        2
    ) as yoy_drug_cost_change_pct

from part_b_agg b
full outer join part_d_agg d on b.data_year = d.data_year
full outer join geo_national g on coalesce(b.data_year, d.data_year) = g.data_year
