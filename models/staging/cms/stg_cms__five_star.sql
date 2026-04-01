-- stg_cms__five_star: Ephemeral staging for nursing home quality ratings
-- Grain: CCN (snapshot)

{{ config(materialized='ephemeral') }}

select
    ccn,
    facility_name,
    provider_state,
    overall_rating,
    health_inspection_rating,
    quality_rating,
    staffing_rating,
    rn_staffing_rating,
    abuse_icon,
    total_weighted_health_survey_score,
    total_number_of_penalties,
    total_fine_amount,
    snapshot_date
from {{ source('staging', 'stg_cms__five_star') }}
