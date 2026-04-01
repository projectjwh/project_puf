-- stg_cms__cahps: Ephemeral staging for CAHPS patient experience
-- Grain: CCN × measure_id

{{ config(materialized='ephemeral') }}

select
    ccn,
    facility_name,
    measure_id,
    measure_name,
    score,
    sample_size,
    footnote,
    start_date,
    end_date
from {{ source('staging', 'stg_cms__cahps') }}
