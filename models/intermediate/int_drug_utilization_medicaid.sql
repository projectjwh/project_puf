-- int_drug_utilization_medicaid: SDUD normalized and aggregated
-- Grain: state × NDC × data_year
-- Value added: Quarterly data → annual aggregation, unit cost calculation

{{ config(
    materialized='table',
    tags=['drug'],
) }}

with sdud as (
    select * from {{ ref('stg_cms__sdud') }}
    where suppression_flag is null or suppression_flag not in ('true', 'Y')
),

state_fips as (
    select state_fips, state_name
    from {{ source('reference', 'ref_state_fips') }}
)

select
    s.state,
    s.state_fips,
    sf.state_name,
    s.ndc,
    s.data_year,
    sum(s.number_of_prescriptions) as total_prescriptions,
    sum(s.total_amount_reimbursed) as total_reimbursed,
    sum(s.medicaid_amount_reimbursed) as total_medicaid_reimbursed,
    sum(s.units_reimbursed) as total_units,
    -- Cost per prescription
    case
        when sum(s.number_of_prescriptions) > 0
        then round(sum(s.total_amount_reimbursed)::numeric / sum(s.number_of_prescriptions), 2)
    end as cost_per_prescription,
    -- Cost per unit
    case
        when sum(s.units_reimbursed) > 0
        then round(sum(s.total_amount_reimbursed)::numeric / sum(s.units_reimbursed), 4)
    end as cost_per_unit,
    count(distinct s.quarter) as quarters_reported
from sdud s
left join state_fips sf on s.state_fips = sf.state_fips
group by s.state, s.state_fips, sf.state_name, s.ndc, s.data_year
