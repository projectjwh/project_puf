-- mart_opioid__by_state: State-level opioid prescribing metrics
-- Grain: state_fips × data_year
-- Value added: aggregated opioid prescribing patterns for Opioid Monitor page

{{ config(
    materialized='table',
    tags=['opioid', 'mart', 'api'],
    indexes=[
        {'columns': ['state_fips', 'data_year'], 'unique': true},
        {'columns': ['data_year']},
    ],
) }}

with prescriptions as (
    select * from {{ ref('int_provider_prescriptions') }}
    where prescriber_state_fips is not null
),

states as (
    select state_fips, state_name, state_abbreviation
    from {{ source('reference', 'ref_state_fips') }}
)

select
    p.prescriber_state_fips as state_fips,
    s.state_name,
    s.state_abbreviation,
    p.data_year,

    -- Prescriber counts
    count(distinct p.prescriber_npi) as total_prescribers,
    count(distinct case when p.has_opioid_prescriptions then p.prescriber_npi end) as opioid_prescribers,
    count(distinct case when p.is_high_opioid_prescriber then p.prescriber_npi end) as high_opioid_prescribers,

    -- Opioid prescriber rate
    round(
        count(distinct case when p.has_opioid_prescriptions then p.prescriber_npi end)::numeric
        / nullif(count(distinct p.prescriber_npi), 0) * 100,
        2
    ) as opioid_prescriber_rate_pct,

    -- Claim volumes
    sum(p.total_claims) as total_rx_claims,
    sum(p.opioid_claims) as total_opioid_claims,
    round(
        sum(p.opioid_claims)::numeric / nullif(sum(p.total_claims), 0) * 100,
        2
    ) as opioid_claim_share_pct,

    -- Opioid spending
    sum(p.opioid_drug_cost) as total_opioid_drug_cost,
    sum(p.total_drug_cost) as total_drug_cost,
    round(
        sum(p.opioid_drug_cost)::numeric / nullif(sum(p.total_drug_cost), 0) * 100,
        2
    ) as opioid_cost_share_pct,

    -- Avg opioid claims per opioid prescriber
    case
        when count(distinct case when p.has_opioid_prescriptions then p.prescriber_npi end) > 0
        then round(
            sum(p.opioid_claims)::numeric
            / count(distinct case when p.has_opioid_prescriptions then p.prescriber_npi end),
            1
        )
    end as avg_opioid_claims_per_prescriber

from prescriptions p
left join states s on p.prescriber_state_fips = s.state_fips
group by p.prescriber_state_fips, s.state_name, s.state_abbreviation, p.data_year
