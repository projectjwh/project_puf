-- mart_drug__medicaid_utilization: State-level Medicaid drug spending
-- Grain: state × data_year
-- Aggregates NDC-level SDUD data to state summaries

{{ config(
    materialized='table',
    tags=['drug'],
) }}

with drug_util as (
    select * from {{ ref('int_drug_utilization_medicaid') }}
)

select
    state,
    state_fips,
    state_name,
    data_year,
    count(distinct ndc) as unique_drugs,
    sum(total_prescriptions) as total_prescriptions,
    sum(total_reimbursed) as total_reimbursed,
    sum(total_medicaid_reimbursed) as total_medicaid_reimbursed,
    sum(total_units) as total_units,
    -- Average cost per prescription across all drugs
    case
        when sum(total_prescriptions) > 0
        then round(sum(total_reimbursed)::numeric / sum(total_prescriptions), 2)
    end as avg_cost_per_prescription,
    -- Total medicaid vs total reimbursed share
    case
        when sum(total_reimbursed) > 0
        then round(sum(total_medicaid_reimbursed)::numeric / sum(total_reimbursed), 4)
    end as medicaid_share_pct
from drug_util
group by state, state_fips, state_name, data_year
