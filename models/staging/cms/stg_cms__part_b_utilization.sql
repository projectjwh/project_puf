-- stg_cms__part_b_utilization: Staging view over Part B utilization data
-- Grain: rendering_npi × hcpcs_code × place_of_service × data_year
-- Value added: type-safe access layer, schema contract isolation
-- Pipeline writes directly to staging.stg_cms__part_b_utilization (partitioned)

{{ config(
    materialized='ephemeral',
    tags=['cms', 'staging', 'utilization'],
) }}

-- Ephemeral because data is pipeline-loaded into staging partition tables.
-- This model serves as documentation and provides a named ref for downstream.

select
    -- Provider
    rendering_npi,
    rendering_npi_name,
    entity_type,
    provider_type,
    medicare_participation,
    provider_state,
    provider_zip5,
    provider_state_fips,

    -- Service
    hcpcs_code,
    hcpcs_description,
    hcpcs_drug_indicator,
    place_of_service,

    -- Counts
    number_of_services,
    number_of_beneficiaries,

    -- Averages (source values)
    avg_submitted_charge,
    avg_medicare_allowed,
    avg_medicare_payment,
    avg_medicare_standardized,

    -- Derived totals (avg × service_count — critical for aggregation)
    total_submitted_charge,
    total_medicare_allowed,
    total_medicare_payment,
    total_medicare_standardized,

    -- Year
    data_year,
    _loaded_at

from {{ source('staging', 'stg_cms__part_b_utilization') }}
where data_year between {{ var('min_data_year') }} and {{ var('max_data_year') }}
