-- mart_postacute__hha_quality: Home Health Agency quality metrics
-- Grain: CCN × data_year

{{ config(
    materialized='table',
    tags=['postacute'],
) }}

with hha as (
    select
        ccn, facility_name, provider_state, provider_state_fips,
        total_episodes, total_hha_charge, total_hha_medicare_payment,
        total_hha_visits, avg_visits_per_episode, data_year
    from {{ source('staging', 'stg_cms__hha_utilization') }}
),

facilities as (
    select ccn, facility_name as pos_name, state
    from {{ source('reference', 'ref_pos_facilities') }}
)

select
    h.ccn,
    h.data_year,
    coalesce(h.facility_name, f.pos_name) as facility_name,
    coalesce(h.provider_state, f.state) as provider_state,
    h.total_episodes,
    h.total_hha_charge,
    h.total_hha_medicare_payment,
    h.total_hha_visits,
    h.avg_visits_per_episode,
    case
        when h.total_episodes > 0
        then round(h.total_hha_medicare_payment::numeric / h.total_episodes, 2)
    end as avg_payment_per_episode
from hha h
left join facilities f on h.ccn = f.ccn
