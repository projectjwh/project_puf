-- int_patient_experience: CAHPS measure pivot — key measures wide per hospital
-- Grain: CCN
-- Value added: Long-form measures → wide format for easy comparison

{{ config(
    materialized='table',
    tags=['quality'],
) }}

with cahps as (
    select * from {{ ref('stg_cms__cahps') }}
),

facilities as (
    select ccn, facility_name, state
    from {{ source('reference', 'ref_pos_facilities') }}
)

select
    c.ccn,
    f.facility_name,
    f.state as provider_state,
    count(distinct c.measure_id) as total_measures_reported,
    avg(c.score) as avg_score_across_measures,
    max(case when c.measure_id like '%COMP_1%' or c.measure_id like '%NURSE_COMM%'
        then c.score end) as nurse_communication_score,
    max(case when c.measure_id like '%COMP_2%' or c.measure_id like '%DOCTOR_COMM%'
        then c.score end) as doctor_communication_score,
    max(case when c.measure_id like '%COMP_5%' or c.measure_id like '%STAFF_RESP%'
        then c.score end) as staff_responsiveness_score,
    max(case when c.measure_id like '%COMP_6%' or c.measure_id like '%DISCHARGE%'
        then c.score end) as discharge_information_score,
    max(case when c.measure_id like '%OVERALL%' or c.measure_id like '%HSP_RATING%'
        then c.score end) as overall_hospital_rating,
    max(case when c.measure_id like '%RECOMMEND%'
        then c.score end) as recommend_hospital_score,
    max(c.sample_size) as max_survey_responses
from cahps c
left join facilities f on c.ccn = f.ccn
group by c.ccn, f.facility_name, f.state
