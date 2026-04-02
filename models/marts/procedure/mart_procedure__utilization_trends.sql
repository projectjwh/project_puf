-- mart_procedure__utilization_trends: Procedure-level utilization trends for API/frontend
-- Grain: hcpcs_code x data_year
-- Value added over intermediate:
--   - Joins RVU reference for complexity weighting
--   - Pre-computed for API response shape (procedure lookup, top-N queries)
--   - Indexed for HCPCS lookup and year filtering

{{ config(
    materialized='table',
    tags=['procedure', 'mart', 'api'],
    indexes=[
        {'columns': ['hcpcs_code', 'data_year']},
        {'columns': ['data_year']},
    ],
) }}

with procedures as (
    select * from {{ ref('int_procedure_utilization') }}
),

-- RVU data for complexity weighting
rvu as (
    select
        hcpcs_code,
        work_rvu,
        facility_pe_rvu,
        malpractice_rvu,
        total_rvu,
        conversion_factor
    from {{ source('reference', 'ref_rvu_fee_schedule') }}
),

-- YOY comparison via self-join
prior_year as (
    select
        hcpcs_code,
        data_year,
        total_services as prior_total_services,
        total_medicare_payment as prior_total_medicare_payment
    from {{ ref('int_procedure_utilization') }}
)

select
    -- Procedure identity
    p.hcpcs_code,
    p.hcpcs_description,
    p.data_year,

    -- Volume
    p.total_services,
    p.total_beneficiaries,
    p.provider_count,

    -- Payment
    p.total_submitted_charge,
    p.total_medicare_payment,
    p.total_medicare_standardized,
    p.avg_payment_per_service,
    p.avg_charge_per_service,
    p.avg_payment_per_beneficiary,

    -- Place-of-service mix
    p.pct_office,
    p.pct_facility,

    -- RVU complexity weighting
    r.work_rvu,
    r.facility_pe_rvu,
    r.malpractice_rvu,
    r.total_rvu,
    r.conversion_factor,

    -- RVU-weighted total (total_services * total_rvu = total wRVUs produced)
    case
        when r.total_rvu is not null
        then round((p.total_services * r.total_rvu)::numeric, 2)
    end as total_rvu_volume,

    -- YOY change
    round(
        (p.total_services - py.prior_total_services)::numeric
        / nullif(py.prior_total_services, 0) * 100,
        2
    ) as yoy_services_change_pct,

    round(
        (p.total_medicare_payment - py.prior_total_medicare_payment)::numeric
        / nullif(py.prior_total_medicare_payment, 0) * 100,
        2
    ) as yoy_payment_change_pct

from procedures p
left join rvu r on p.hcpcs_code = r.hcpcs_code
left join prior_year py
    on p.hcpcs_code = py.hcpcs_code
    and p.data_year = py.data_year + 1
