-- int_procedure_utilization: Procedure-level utilization from Part B
-- Grain: hcpcs_code x data_year
-- Value added over staging:
--   - Aggregates from provider-service-line to procedure-year level
--   - Uses TOTALS (derived from averages in pipeline) -- NOT raw averages
--   - Computes provider counts, payment averages, place-of-service mix
--   - Without this aggregation layer, procedure comparison is impossible

{{ config(
    materialized='table',
    tags=['intermediate', 'procedure'],
) }}

with part_b as (
    select * from {{ ref('stg_cms__part_b_utilization') }}
),

-- Place-of-service breakdowns per procedure-year
pos_breakdown as (
    select
        hcpcs_code,
        data_year,
        sum(case when place_of_service = 'O' then number_of_services else 0 end) as office_services,
        sum(case when place_of_service = 'F' then number_of_services else 0 end) as facility_services,
        sum(number_of_services) as total_services_for_pct
    from part_b
    group by hcpcs_code, data_year
),

-- Main aggregation at procedure-year grain
procedure_agg as (
    select
        hcpcs_code,
        -- Use the most common description across providers
        mode() within group (order by hcpcs_description) as hcpcs_description,
        data_year,

        -- Volume
        sum(number_of_services) as total_services,
        sum(number_of_beneficiaries) as total_beneficiaries,
        count(distinct rendering_npi) as provider_count,

        -- Payment totals (using pipeline-derived totals, NOT averages)
        sum(total_submitted_charge) as total_submitted_charge,
        sum(total_medicare_allowed) as total_medicare_allowed,
        sum(total_medicare_payment) as total_medicare_payment,
        sum(total_medicare_standardized) as total_medicare_standardized,

        -- Per-service averages (re-derived from proper totals)
        case
            when sum(number_of_services) > 0
            then round(sum(total_medicare_payment)::numeric / sum(number_of_services), 2)
        end as avg_payment_per_service,

        case
            when sum(number_of_services) > 0
            then round(sum(total_submitted_charge)::numeric / sum(number_of_services), 2)
        end as avg_charge_per_service,

        -- Per-beneficiary average
        case
            when sum(number_of_beneficiaries) > 0
            then round(sum(total_medicare_payment)::numeric / sum(number_of_beneficiaries), 2)
        end as avg_payment_per_beneficiary

    from part_b
    group by hcpcs_code, data_year
)

select
    pa.hcpcs_code,
    pa.hcpcs_description,
    pa.data_year,

    -- Volume
    pa.total_services,
    pa.total_beneficiaries,
    pa.provider_count,

    -- Payment totals
    pa.total_submitted_charge,
    pa.total_medicare_allowed,
    pa.total_medicare_payment,
    pa.total_medicare_standardized,

    -- Per-unit averages
    pa.avg_payment_per_service,
    pa.avg_charge_per_service,
    pa.avg_payment_per_beneficiary,

    -- Place-of-service mix
    case
        when pos.total_services_for_pct > 0
        then round(pos.office_services::numeric / pos.total_services_for_pct * 100, 1)
    end as pct_office,

    case
        when pos.total_services_for_pct > 0
        then round(pos.facility_services::numeric / pos.total_services_for_pct * 100, 1)
    end as pct_facility

from procedure_agg pa
left join pos_breakdown pos on pa.hcpcs_code = pos.hcpcs_code and pa.data_year = pos.data_year
