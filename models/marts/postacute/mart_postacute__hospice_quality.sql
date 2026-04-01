-- mart_postacute__hospice_quality: Hospice quality metrics
-- Grain: CCN × data_year

{{ config(
    materialized='table',
    tags=['postacute'],
) }}

with hospice as (
    select
        ccn, facility_name, provider_state, provider_state_fips,
        total_beneficiaries, total_hospice_charge, total_hospice_medicare_payment,
        total_hospice_days, avg_length_of_stay, data_year
    from {{ source('staging', 'stg_cms__hospice_utilization') }}
),

facilities as (
    select ccn, facility_name as pos_name, state
    from {{ source('reference', 'ref_pos_facilities') }}
)

select
    h.ccn,
    h.data_year,
    coalesce(h.facility_name, f.pos_name) as facility_name,
    coalesce(h.provider_state, f.state) as provider_state,
    h.total_beneficiaries,
    h.total_hospice_charge,
    h.total_hospice_medicare_payment,
    h.total_hospice_days,
    h.avg_length_of_stay,
    case
        when h.total_beneficiaries > 0
        then round(h.total_hospice_medicare_payment::numeric / h.total_beneficiaries, 2)
    end as avg_payment_per_beneficiary
from hospice h
left join facilities f on h.ccn = f.ccn
