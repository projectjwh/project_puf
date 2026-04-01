-- int_hospital_discharges: Hospital discharge analysis with DRG weights
-- Grain: CCN × data_year
-- Value added: DRG weight join, case mix index (CMI) computation,
--   total revenue aggregation across DRGs per hospital

{{ config(
    materialized='table',
    tags=['hospital'],
) }}

with inpatient as (
    select * from {{ ref('stg_cms__inpatient') }}
),

drg_weights as (
    select
        drg_code,
        relative_weight
    from {{ source('reference', 'ref_msdrg') }}
),

facilities as (
    select
        ccn,
        facility_name,
        facility_type,
        state
    from {{ source('reference', 'ref_pos_facilities') }}
),

-- Join DRG weights to compute weighted discharges
discharge_detail as (
    select
        i.ccn,
        i.data_year,
        i.drg_code,
        i.total_discharges,
        i.total_covered_charges,
        i.total_payments,
        i.total_medicare_payments,
        coalesce(d.relative_weight, 1.0) as drg_weight,
        i.total_discharges * coalesce(d.relative_weight, 1.0) as weighted_discharges
    from inpatient i
    left join drg_weights d on i.drg_code = d.drg_code
)

select
    dd.ccn,
    dd.data_year,
    f.facility_name,
    f.facility_type,
    f.state as provider_state,
    count(distinct dd.drg_code) as unique_drg_count,
    sum(dd.total_discharges) as total_discharges,
    sum(dd.weighted_discharges) as total_weighted_discharges,
    -- Case Mix Index = weighted discharges / total discharges
    case
        when sum(dd.total_discharges) > 0
        then round(sum(dd.weighted_discharges)::numeric / sum(dd.total_discharges), 4)
    end as case_mix_index,
    sum(dd.total_covered_charges) as total_covered_charges,
    sum(dd.total_payments) as total_payments,
    sum(dd.total_medicare_payments) as total_medicare_payments,
    case
        when sum(dd.total_discharges) > 0
        then round(sum(dd.total_medicare_payments)::numeric / sum(dd.total_discharges), 2)
    end as avg_payment_per_discharge
from discharge_detail dd
left join facilities f on dd.ccn = f.ccn
group by dd.ccn, dd.data_year, f.facility_name, f.facility_type, f.state
