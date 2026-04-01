-- stg_cms__part_d_prescribers: Staging view over Part D prescriber data
-- Grain: prescriber_npi × drug_name × generic_name × data_year
-- Value added: type-safe access layer, schema contract isolation

{{ config(
    materialized='ephemeral',
    tags=['cms', 'staging', 'utilization'],
) }}

select
    -- Prescriber
    prescriber_npi,
    prescriber_last_name,
    prescriber_first_name,
    prescriber_state,
    prescriber_state_fips,
    specialty_description,

    -- Drug
    drug_name,
    generic_name,
    is_brand_name,
    is_generic,

    -- Claims
    total_claim_count,
    total_day_supply,
    total_drug_cost,
    total_beneficiary_count,

    -- Derived cost metrics
    cost_per_claim,
    cost_per_day,

    -- Opioid flags
    is_opioid,
    opioid_claim_count,
    opioid_prescriber_rate,

    -- Suppression
    ge65_suppress_flag,

    -- Year
    data_year,
    _loaded_at

from {{ source('staging', 'stg_cms__part_d_prescribers') }}
where data_year between {{ var('min_data_year') }} and {{ var('max_data_year') }}
