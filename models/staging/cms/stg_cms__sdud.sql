-- stg_cms__sdud: Ephemeral staging for State Drug Utilization Data
-- Grain: state × NDC × year × quarter

{{ config(materialized='ephemeral') }}

select
    state,
    state_fips,
    ndc,
    labeler_code,
    product_code,
    package_size,
    year,
    quarter,
    suppression_flag,
    utilization_type,
    number_of_prescriptions,
    total_amount_reimbursed,
    medicaid_amount_reimbursed,
    non_medicaid_amount_reimbursed,
    units_reimbursed,
    data_year
from {{ source('staging', 'stg_cms__sdud') }}
where data_year between {{ var('min_data_year') }} and {{ var('max_data_year') }}
