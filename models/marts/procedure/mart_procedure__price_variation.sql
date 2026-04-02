-- mart_procedure__price_variation: Price variation for same procedure across states
-- Grain: hcpcs_code x provider_state x data_year
-- Value added over staging:
--   - Aggregates to procedure-state-year level
--   - Computes distribution statistics (min, max, p25, p75, stddev, CV)
--   - Enables "same procedure, different prices" analysis
--   - Indexed for HCPCS lookup and state filtering

{{ config(
    materialized='table',
    tags=['procedure', 'mart', 'api'],
    indexes=[
        {'columns': ['hcpcs_code', 'data_year']},
        {'columns': ['provider_state']},
    ],
) }}

with part_b as (
    select * from {{ ref('stg_cms__part_b_utilization') }}
),

-- Compute per-provider average payment for each procedure-state-year
-- This gives us the distribution of provider-level payment rates
provider_level as (
    select
        hcpcs_code,
        provider_state,
        data_year,
        rendering_npi,

        -- Provider-level average payment per service for this HCPCS
        case
            when sum(number_of_services) > 0
            then sum(total_medicare_payment)::numeric / sum(number_of_services)
        end as provider_avg_payment_per_service

    from part_b
    where provider_state is not null
    group by hcpcs_code, provider_state, data_year, rendering_npi
),

-- State-level aggregation with distribution stats
state_agg as (
    select
        hcpcs_code,
        provider_state,
        data_year,

        count(distinct rendering_npi) as provider_count,
        round(avg(provider_avg_payment_per_service)::numeric, 2) as avg_payment,
        round(min(provider_avg_payment_per_service)::numeric, 2) as min_payment,
        round(max(provider_avg_payment_per_service)::numeric, 2) as max_payment,
        round(stddev(provider_avg_payment_per_service)::numeric, 2) as stddev_payment,

        -- Percentiles
        round(percentile_cont(0.25) within group (order by provider_avg_payment_per_service)::numeric, 2) as p25_payment,
        round(percentile_cont(0.75) within group (order by provider_avg_payment_per_service)::numeric, 2) as p75_payment

    from provider_level
    where provider_avg_payment_per_service is not null
    group by hcpcs_code, provider_state, data_year
),

-- Overall procedure totals for context
procedure_totals as (
    select
        hcpcs_code,
        provider_state,
        data_year,
        sum(number_of_services) as total_services,
        sum(total_medicare_payment) as total_medicare_payment,
        mode() within group (order by hcpcs_description) as hcpcs_description
    from part_b
    where provider_state is not null
    group by hcpcs_code, provider_state, data_year
)

select
    sa.hcpcs_code,
    pt.hcpcs_description,
    sa.provider_state,
    sa.data_year,

    -- Volume
    sa.provider_count,
    pt.total_services,
    pt.total_medicare_payment,

    -- Price distribution across providers in this state
    sa.avg_payment,
    sa.min_payment,
    sa.max_payment,
    sa.stddev_payment,
    sa.p25_payment,
    sa.p75_payment,

    -- Coefficient of variation: stddev / mean (higher = more price variation)
    case
        when sa.avg_payment > 0
        then round(sa.stddev_payment / sa.avg_payment, 4)
    end as coefficient_of_variation

from state_agg sa
inner join procedure_totals pt
    on sa.hcpcs_code = pt.hcpcs_code
    and sa.provider_state = pt.provider_state
    and sa.data_year = pt.data_year
