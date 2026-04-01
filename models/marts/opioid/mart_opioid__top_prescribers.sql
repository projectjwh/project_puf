-- mart_opioid__top_prescribers: High-volume opioid prescribers
-- Grain: prescriber_npi × data_year
-- Value added: identifies outlier opioid prescribers with provider context

{{ config(
    materialized='table',
    tags=['opioid', 'mart', 'api'],
    indexes=[
        {'columns': ['prescriber_npi', 'data_year']},
        {'columns': ['prescriber_state_fips', 'data_year']},
        {'columns': ['data_year']},
    ],
) }}

with prescriptions as (
    select * from {{ ref('int_provider_prescriptions') }}
    where has_opioid_prescriptions = true
),

providers as (
    select
        npi,
        display_name,
        specialty_classification,
        practice_state,
        practice_city,
        practice_zip5,
        state_fips
    from {{ ref('int_providers') }}
)

select
    rx.prescriber_npi,
    rx.data_year,

    -- Provider identity
    p.display_name,
    p.specialty_classification,
    rx.specialty_description as partd_specialty,
    p.practice_state,
    p.practice_city,
    p.practice_zip5,
    rx.prescriber_state_fips,

    -- Overall prescribing
    rx.total_claims,
    rx.total_drug_cost,
    rx.unique_drugs_prescribed,
    rx.total_beneficiaries,

    -- Opioid specifics
    rx.opioid_claims,
    rx.opioid_drug_cost,
    rx.unique_opioids_prescribed,
    rx.opioid_claim_rate_pct,
    rx.is_high_opioid_prescriber,

    -- Generic prescribing
    rx.generic_rate_pct,

    -- Ranking within state-year
    rank() over (
        partition by rx.prescriber_state_fips, rx.data_year
        order by rx.opioid_claims desc nulls last
    ) as state_opioid_rank

from prescriptions rx
left join providers p on rx.prescriber_npi = p.npi
