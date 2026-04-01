-- mart_hospital__readmissions: Hospital readmission performance
-- Grain: CCN × data_year

{{ config(
    materialized='table',
    tags=['hospital', 'quality'],
) }}

select
    ccn,
    facility_name,
    provider_state,
    data_year,
    measure_count,
    avg_readmission_rate,
    measures_worse_than_national,
    measures_better_than_national,
    measures_no_different,
    has_penalty_risk
from {{ ref('int_hospital_readmissions') }}
