-- mart_provider__practice_profile: Provider practice profile for API/frontend
-- Grain: one row per NPI (latest year of utilization data)
-- Value added over intermediate:
--   - Cross-source fusion: NPPES identity + Part B services + Part D prescribing
--   - Pre-computed for API response shape
--   - Indexed for NPI lookup (<10ms target)
--   - Includes all fields needed by Provider Lookup page

{{ config(
    materialized='table',
    tags=['provider', 'mart', 'api'],
    indexes=[
        {'columns': ['npi'], 'unique': true},
        {'columns': ['practice_state']},
        {'columns': ['primary_taxonomy_code']},
        {'columns': ['state_fips']},
        {'columns': ['practice_zip5']},
    ],
) }}

with providers as (
    select * from {{ ref('int_providers') }}
),

-- Latest year of Part B data per provider
services as (
    select
        rendering_npi,
        data_year as services_data_year,
        total_services,
        total_beneficiaries,
        total_medicare_payments,
        total_medicare_standardized,
        unique_hcpcs_count,
        payment_per_beneficiary,
        em_services_pct,
        drug_services_pct,
        provider_type as partb_provider_type
    from {{ ref('int_provider_services') }}
    where data_year = {{ var('max_data_year') }}
),

-- Latest year of Part D data per provider
prescriptions as (
    select
        prescriber_npi,
        data_year as prescribing_data_year,
        total_claims as total_rx_claims,
        total_drug_cost,
        unique_drugs_prescribed,
        generic_rate_pct,
        has_opioid_prescriptions,
        opioid_claims,
        opioid_claim_rate_pct,
        is_high_opioid_prescriber,
        avg_cost_per_claim as avg_rx_cost_per_claim,
        brand_drug_cost,
        generic_drug_cost
    from {{ ref('int_provider_prescriptions') }}
    where data_year = {{ var('max_data_year') }}
)

select
    -- Identity (from NPPES via int_providers)
    p.npi,
    p.entity_type,
    p.display_name,
    p.provider_last_name,
    p.provider_first_name,
    p.provider_credential,
    p.provider_organization_name,
    p.gender,

    -- Location
    p.practice_address_line_1,
    p.practice_city,
    p.practice_state,
    p.practice_zip5,
    p.state_fips,
    p.state_name,
    p.census_region,

    -- Specialty
    p.primary_taxonomy_code,
    p.specialty_classification,
    p.specialty_specialization,
    p.specialty_display_name,
    p.taxonomy_count,

    -- Provider attributes
    p.is_individual,
    p.is_organization,
    p.enumeration_date,
    p.years_since_enumeration,

    -- Part B: Service utilization
    s.services_data_year,
    s.total_services as total_services_rendered,
    s.total_beneficiaries as total_beneficiaries_served,
    s.total_medicare_payments,
    s.total_medicare_standardized,
    s.unique_hcpcs_count,
    s.payment_per_beneficiary,
    s.em_services_pct,
    s.drug_services_pct,
    coalesce(s.partb_provider_type, p.specialty_classification) as medicare_provider_type,

    -- Part D: Prescribing
    rx.prescribing_data_year,
    rx.total_rx_claims as total_drugs_prescribed,
    rx.total_drug_cost,
    rx.unique_drugs_prescribed,
    rx.generic_rate_pct,
    rx.avg_rx_cost_per_claim,
    rx.has_opioid_prescriptions,
    rx.opioid_claims,
    rx.opioid_claim_rate_pct,
    rx.is_high_opioid_prescriber,

    -- Data completeness flags
    case when s.rendering_npi is not null then true else false end as has_part_b_data,
    case when rx.prescriber_npi is not null then true else false end as has_part_d_data,

    p._loaded_at

from providers p
left join services s on p.npi = s.rendering_npi
left join prescriptions rx on p.npi = rx.prescriber_npi
