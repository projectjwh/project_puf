-- int_hospital_financials: Hospital financial metrics from cost reports
-- Grain: CCN × data_year
-- Value added: Named financial metrics from raw worksheets,
--   derived ratios (operating margin, cost-to-charge), facility info join

{{ config(
    materialized='table',
    tags=['hospital', 'financial'],
) }}

with cost_reports as (
    select
        rpt_rec_num,
        ccn,
        report_status_code,
        fiscal_year_begin,
        fiscal_year_end,
        total_patient_revenue,
        total_operating_expenses,
        net_income,
        total_beds_available,
        total_patient_days,
        total_discharges,
        operating_margin,
        cost_to_charge_ratio,
        data_year
    from {{ source('staging', 'stg_cms__cost_reports_snf') }}
    -- Union with other cost report types as they become available
    union all
    select
        rpt_rec_num, ccn, report_status_code,
        fiscal_year_begin, fiscal_year_end,
        total_patient_revenue, total_operating_expenses, net_income,
        total_beds_available, total_patient_days, total_discharges,
        operating_margin, cost_to_charge_ratio, data_year
    from {{ source('staging', 'stg_cms__cost_reports_hha') }}
    union all
    select
        rpt_rec_num, ccn, report_status_code,
        fiscal_year_begin, fiscal_year_end,
        total_patient_revenue, total_operating_expenses, net_income,
        total_beds_available, total_patient_days, total_discharges,
        operating_margin, cost_to_charge_ratio, data_year
    from {{ source('staging', 'stg_cms__cost_reports_hospice') }}
),

facilities as (
    select ccn, facility_name, facility_type, state, ownership_type
    from {{ source('reference', 'ref_pos_facilities') }}
)

select
    cr.ccn,
    cr.data_year,
    f.facility_name,
    f.facility_type,
    f.state as provider_state,
    f.ownership_type,
    cr.fiscal_year_begin,
    cr.fiscal_year_end,
    cr.total_patient_revenue,
    cr.total_operating_expenses,
    cr.net_income,
    cr.total_beds_available,
    cr.total_patient_days,
    cr.total_discharges,
    cr.operating_margin,
    cr.cost_to_charge_ratio,
    -- Revenue per discharge
    case
        when cr.total_discharges > 0
        then round(cr.total_patient_revenue::numeric / cr.total_discharges, 2)
    end as revenue_per_discharge,
    -- Average daily census
    case
        when cr.fiscal_year_begin is not null and cr.fiscal_year_end is not null
        then round(cr.total_patient_days::numeric / 365, 1)
    end as avg_daily_census,
    -- Occupancy rate
    case
        when cr.total_beds_available > 0
        then round(cr.total_patient_days::numeric / (cr.total_beds_available * 365), 4)
    end as occupancy_rate
from cost_reports cr
left join facilities f on cr.ccn = f.ccn
