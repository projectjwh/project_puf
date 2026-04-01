-- mart_hospital__financial_profile: Hospital financial summary for API/dashboard
-- Grain: CCN × data_year
-- Cross-source: Cost reports + POS facilities + hospital general info

{{ config(
    materialized='table',
    tags=['hospital', 'financial'],
) }}

with financials as (
    select * from {{ ref('int_hospital_financials') }}
),

hospital_info as (
    select
        ccn,
        hospital_type,
        hospital_ownership,
        overall_rating,
        emergency_services
    from {{ source('reference_tier2', 'ref_hospital_general') }}
)

select
    f.ccn,
    f.data_year,
    f.facility_name,
    f.provider_state,
    f.facility_type,
    coalesce(h.hospital_type, f.facility_type) as hospital_type,
    coalesce(h.hospital_ownership, f.ownership_type) as ownership_type,
    h.overall_rating as cms_overall_rating,
    h.emergency_services,
    f.total_patient_revenue,
    f.total_operating_expenses,
    f.net_income,
    f.operating_margin,
    f.cost_to_charge_ratio,
    f.total_beds_available,
    f.total_discharges,
    f.total_patient_days,
    f.occupancy_rate,
    f.revenue_per_discharge,
    f.avg_daily_census
from financials f
left join hospital_info h on f.ccn = h.ccn
