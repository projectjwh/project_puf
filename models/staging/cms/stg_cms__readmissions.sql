-- stg_cms__readmissions: Ephemeral staging for hospital readmissions
-- Grain: CCN × measure_id

{{ config(materialized='ephemeral') }}

select
    ccn,
    facility_name,
    provider_state,
    measure_id,
    measure_name,
    denominator,
    score,
    lower_estimate,
    upper_estimate,
    compared_to_national,
    data_year
from {{ source('staging', 'stg_cms__readmissions') }}
