-- mart_hospital__performance: Hospital discharge performance with DRG mix
-- Grain: CCN × data_year

{{ config(
    materialized='table',
    tags=['hospital'],
) }}

with discharges as (
    select * from {{ ref('int_hospital_discharges') }}
),

hospital_info as (
    select ccn, hospital_type, overall_rating
    from {{ source('reference_tier2', 'ref_hospital_general') }}
)

select
    d.ccn,
    d.data_year,
    d.facility_name,
    d.provider_state,
    h.hospital_type,
    h.overall_rating as cms_overall_rating,
    d.unique_drg_count,
    d.total_discharges,
    d.case_mix_index,
    d.total_covered_charges,
    d.total_payments,
    d.total_medicare_payments,
    d.avg_payment_per_discharge
from discharges d
left join hospital_info h on d.ccn = h.ccn
