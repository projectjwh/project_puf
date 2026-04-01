-- stg_cms__charges: Ephemeral staging for hospital charges
-- Grain: CCN × DRG × data_year

{{ config(materialized='ephemeral') }}

select
    ccn,
    facility_name,
    provider_state,
    provider_state_fips,
    drg_code,
    drg_description,
    total_discharges,
    avg_covered_charges,
    avg_total_payments,
    avg_medicare_payments,
    total_covered_charges,
    total_payments,
    total_medicare_payments,
    data_year
from {{ source('staging', 'stg_cms__charges') }}
where data_year between {{ var('min_data_year') }} and {{ var('max_data_year') }}
