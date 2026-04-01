-- int_provider_services: Provider-level service summary from Part B
-- Grain: rendering_npi × data_year
-- Value added over staging:
--   - Aggregates from service-line to provider-year level
--   - Uses TOTALS (derived from averages in pipeline) — NOT raw averages
--   - Computes unique HCPCS count, beneficiary count, payment amounts
--   - Categorizes services (E&M, procedures, drugs, etc.)
--   - Without this aggregation layer, provider comparison is impossible

{{ config(
    materialized='table',
    tags=['intermediate', 'utilization', 'provider'],
) }}

with part_b as (
    select * from {{ ref('stg_cms__part_b_utilization') }}
),

-- Service categorization based on HCPCS code ranges
categorized as (
    select
        rendering_npi,
        data_year,
        hcpcs_code,
        number_of_services,
        number_of_beneficiaries,
        total_submitted_charge,
        total_medicare_allowed,
        total_medicare_payment,
        total_medicare_standardized,
        provider_type,
        provider_state,
        provider_state_fips,
        hcpcs_drug_indicator,

        -- E&M services: 99201-99499
        case
            when hcpcs_code between '99201' and '99499' then true
            else false
        end as is_em_service,

        -- Drug administration: J-codes
        case
            when hcpcs_code like 'J%' or hcpcs_drug_indicator = 'Y' then true
            else false
        end as is_drug_service,

        -- Imaging: 70010-79999
        case
            when hcpcs_code between '70010' and '79999' then true
            else false
        end as is_imaging_service,

        -- Surgery: 10004-69990
        case
            when hcpcs_code between '10004' and '69990' then true
            else false
        end as is_surgical_service

    from part_b
)

select
    rendering_npi,
    data_year,

    -- Provider context (from most common row)
    mode() within group (order by provider_type) as provider_type,
    mode() within group (order by provider_state) as provider_state,
    mode() within group (order by provider_state_fips) as provider_state_fips,

    -- Service counts
    count(distinct hcpcs_code) as unique_hcpcs_count,
    sum(number_of_services) as total_services,
    sum(number_of_beneficiaries) as total_beneficiaries,

    -- Payment totals (using pipeline-derived totals, NOT averages)
    sum(total_submitted_charge) as total_submitted_charges,
    sum(total_medicare_allowed) as total_medicare_allowed,
    sum(total_medicare_payment) as total_medicare_payments,
    sum(total_medicare_standardized) as total_medicare_standardized,

    -- Per-beneficiary averages (re-derived from proper totals)
    case
        when sum(number_of_beneficiaries) > 0
        then round(sum(total_medicare_payment)::numeric / sum(number_of_beneficiaries), 2)
    end as payment_per_beneficiary,

    -- Service mix
    sum(case when is_em_service then number_of_services else 0 end) as em_services,
    sum(case when is_drug_service then number_of_services else 0 end) as drug_services,
    sum(case when is_imaging_service then number_of_services else 0 end) as imaging_services,
    sum(case when is_surgical_service then number_of_services else 0 end) as surgical_services,

    -- Service mix percentages
    case
        when sum(number_of_services) > 0
        then round(sum(case when is_em_service then number_of_services else 0 end)::numeric
                    / sum(number_of_services) * 100, 1)
    end as em_services_pct,

    case
        when sum(number_of_services) > 0
        then round(sum(case when is_drug_service then number_of_services else 0 end)::numeric
                    / sum(number_of_services) * 100, 1)
    end as drug_services_pct

from categorized
group by rendering_npi, data_year
