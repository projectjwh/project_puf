-- int_provider_prescriptions: Provider-level prescribing summary from Part D
-- Grain: prescriber_npi × data_year
-- Value added over staging:
--   - Aggregates from drug-level to provider-year level
--   - Computes total drug cost, claim counts, unique drugs
--   - Derives opioid prescribing metrics (% of claims, total opioid cost)
--   - Brand vs. generic split
--   - Without this, cross-provider prescribing comparison is impossible

{{ config(
    materialized='table',
    tags=['intermediate', 'utilization', 'provider'],
) }}

with part_d as (
    select * from {{ ref('stg_cms__part_d_prescribers') }}
)

select
    prescriber_npi,
    data_year,

    -- Prescriber context
    mode() within group (order by specialty_description) as specialty_description,
    mode() within group (order by prescriber_state) as prescriber_state,
    mode() within group (order by prescriber_state_fips) as prescriber_state_fips,

    -- Overall prescribing volume
    count(distinct generic_name) as unique_drugs_prescribed,
    sum(total_claim_count) as total_claims,
    sum(total_day_supply) as total_day_supply,
    sum(total_drug_cost) as total_drug_cost,
    sum(total_beneficiary_count) as total_beneficiaries,

    -- Cost metrics
    case
        when sum(total_claim_count) > 0
        then round(sum(total_drug_cost)::numeric / sum(total_claim_count), 2)
    end as avg_cost_per_claim,

    case
        when sum(total_day_supply) > 0
        then round(sum(total_drug_cost)::numeric / sum(total_day_supply), 2)
    end as avg_cost_per_day,

    -- Brand vs. generic
    sum(case when is_brand_name then total_claim_count else 0 end) as brand_claims,
    sum(case when is_generic then total_claim_count else 0 end) as generic_claims,
    case
        when sum(total_claim_count) > 0
        then round(sum(case when is_generic then total_claim_count else 0 end)::numeric
                    / sum(total_claim_count) * 100, 1)
    end as generic_rate_pct,

    -- Brand cost vs generic cost
    sum(case when is_brand_name then total_drug_cost else 0 end) as brand_drug_cost,
    sum(case when is_generic then total_drug_cost else 0 end) as generic_drug_cost,

    -- Opioid prescribing
    sum(case when is_opioid then total_claim_count else 0 end) as opioid_claims,
    sum(case when is_opioid then total_drug_cost else 0 end) as opioid_drug_cost,
    count(distinct case when is_opioid then generic_name end) as unique_opioids_prescribed,

    case
        when sum(total_claim_count) > 0
        then round(sum(case when is_opioid then total_claim_count else 0 end)::numeric
                    / sum(total_claim_count) * 100, 2)
    end as opioid_claim_rate_pct,

    -- Opioid prescriber flag (>10% of claims are opioids, or any opioid claims)
    case
        when sum(case when is_opioid then total_claim_count else 0 end) > 0 then true
        else false
    end as has_opioid_prescriptions,

    -- High opioid prescriber flag (>20% of claims are opioids)
    case
        when sum(total_claim_count) > 0
         and sum(case when is_opioid then total_claim_count else 0 end)::numeric
             / sum(total_claim_count) > 0.20 then true
        else false
    end as is_high_opioid_prescriber

from part_d
group by prescriber_npi, data_year
