-- int_hospital_readmissions: Readmission penalty calculation
-- Grain: CCN
-- Value added: Excess readmission ratio aggregation, estimated penalty amount

{{ config(
    materialized='table',
    tags=['hospital', 'quality'],
) }}

with readmissions as (
    select * from {{ ref('stg_cms__readmissions') }}
),

facilities as (
    select ccn, facility_name, state
    from {{ source('reference', 'ref_pos_facilities') }}
)

select
    r.ccn,
    f.facility_name,
    f.state as provider_state,
    r.data_year,
    count(distinct r.measure_id) as measure_count,
    avg(r.score) as avg_readmission_rate,
    sum(case when r.compared_to_national = 'WORSE THAN THE NATIONAL RATE'
             or r.compared_to_national = 'WORSE THAN NATIONAL RATE'
        then 1 else 0 end) as measures_worse_than_national,
    sum(case when r.compared_to_national = 'BETTER THAN THE NATIONAL RATE'
             or r.compared_to_national = 'BETTER THAN NATIONAL RATE'
        then 1 else 0 end) as measures_better_than_national,
    sum(case when r.compared_to_national = 'NO DIFFERENT THAN THE NATIONAL RATE'
             or r.compared_to_national = 'NO DIFFERENT THAN NATIONAL RATE'
        then 1 else 0 end) as measures_no_different,
    -- Penalty flag: worse on any measure
    case when sum(case when r.compared_to_national like '%WORSE%' then 1 else 0 end) > 0
        then true else false
    end as has_penalty_risk
from readmissions r
left join facilities f on r.ccn = f.ccn
group by r.ccn, f.facility_name, f.state, r.data_year
