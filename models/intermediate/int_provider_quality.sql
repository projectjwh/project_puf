-- int_provider_quality: Facility-level quality composite from Five-Star + Readmissions
-- Grain: CCN × data_year (facility-level; join to provider profile via POS CCN → state)
-- Value added: Merges nursing home quality ratings with hospital readmission penalties
--   into a single facility quality summary. Enables provider-quality mart joins.

{{ config(
    materialized='table',
    tags=['provider', 'quality'],
) }}

with five_star as (
    select
        ccn,
        facility_name,
        provider_state,
        overall_rating,
        health_inspection_rating,
        quality_rating,
        staffing_rating,
        rn_staffing_rating,
        total_number_of_penalties,
        total_fine_amount,
        snapshot_date
    from {{ ref('stg_cms__five_star') }}
),

readmissions_agg as (
    select
        ccn,
        data_year,
        count(distinct measure_id) as readmission_measure_count,
        avg(score) as avg_readmission_rate,
        sum(case when compared_to_national like '%WORSE%' then 1 else 0 end) as measures_worse_than_national,
        sum(case when compared_to_national like '%BETTER%' then 1 else 0 end) as measures_better_than_national,
        sum(case when compared_to_national like '%NO DIFFERENT%' then 1 else 0 end) as measures_no_different,
        case when sum(case when compared_to_national like '%WORSE%' then 1 else 0 end) > 0
            then true else false
        end as has_readmission_penalty_risk
    from {{ ref('stg_cms__readmissions') }}
    group by ccn, data_year
),

facilities as (
    select ccn, facility_name, facility_type, state
    from {{ source('reference', 'ref_pos_facilities') }}
)

select
    -- Use coalesce to capture facilities from either source
    coalesce(fs.ccn, ra.ccn) as ccn,
    coalesce(f.facility_name, fs.facility_name) as facility_name,
    f.facility_type,
    coalesce(f.state, fs.provider_state) as provider_state,

    -- Five-Star ratings (nursing homes)
    fs.overall_rating,
    fs.health_inspection_rating,
    fs.quality_rating,
    fs.staffing_rating,
    fs.rn_staffing_rating,
    fs.total_number_of_penalties,
    fs.total_fine_amount,
    fs.snapshot_date as five_star_snapshot_date,

    -- Readmissions (hospitals)
    ra.data_year as readmissions_data_year,
    ra.readmission_measure_count,
    ra.avg_readmission_rate,
    ra.measures_worse_than_national,
    ra.measures_better_than_national,
    ra.measures_no_different,
    ra.has_readmission_penalty_risk,

    -- Quality flags
    case when fs.ccn is not null then true else false end as has_five_star_data,
    case when ra.ccn is not null then true else false end as has_readmissions_data,

    -- Composite quality tier (where applicable)
    case
        when fs.overall_rating >= 4 then 'HIGH'
        when fs.overall_rating >= 3 then 'MEDIUM'
        when fs.overall_rating >= 1 then 'LOW'
    end as five_star_quality_tier,

    case
        when ra.has_readmission_penalty_risk = true then 'AT_RISK'
        when ra.measures_better_than_national > 0 then 'ABOVE_AVERAGE'
        when ra.ccn is not null then 'AVERAGE'
    end as readmission_quality_tier

from five_star fs
full outer join readmissions_agg ra on fs.ccn = ra.ccn
left join facilities f on coalesce(fs.ccn, ra.ccn) = f.ccn
