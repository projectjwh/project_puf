-- mart_provider__historical_profile: Historized provider profile with SCD Type 2 versioning
-- Grain: one row per NPI x validity period (dbt_valid_from, dbt_valid_to)
-- Tracks: taxonomy changes, state changes, active/inactive transitions
-- Derived: version_number, is_current, days_in_version, previous_state, previous_taxonomy

{{ config(
    materialized='table',
    tags=['mart', 'provider', 'scd'],
    indexes=[
        {'columns': ['npi', 'dbt_valid_from']},
        {'columns': ['npi'], 'unique': false},
        {'columns': ['practice_state', 'dbt_valid_from']},
    ],
) }}

with snapshot_base as (
    select
        npi,
        entity_type,
        display_name,
        primary_taxonomy_code,
        practice_state,
        practice_city,
        practice_zip5,
        state_fips,
        is_active,
        is_individual,
        is_organization,
        provider_credential,
        taxonomy_count,
        enumeration_date,
        deactivation_date,
        dbt_valid_from,
        dbt_valid_to,
        dbt_scd_id,
        _snapshot_ts
    from {{ ref('snp_provider_history') }}
),

versioned as (
    select
        *,
        row_number() over (
            partition by npi
            order by dbt_valid_from
        ) as version_number,
        case when dbt_valid_to is null then true else false end as is_current,
        case
            when dbt_valid_to is not null
                then extract(day from dbt_valid_to - dbt_valid_from)
            else extract(day from current_timestamp - dbt_valid_from)
        end as days_in_version,
        lag(practice_state) over (
            partition by npi
            order by dbt_valid_from
        ) as previous_state,
        lag(primary_taxonomy_code) over (
            partition by npi
            order by dbt_valid_from
        ) as previous_taxonomy
    from snapshot_base
),

taxonomy as (
    select
        taxonomy_code,
        classification as specialty_classification,
        specialization as specialty_specialization,
        display_name as specialty_display_name,
        grouping as specialty_grouping
    from {{ source('reference', 'ref_nucc_taxonomy') }}
)

select
    -- Provider identity
    v.npi,
    v.entity_type,
    v.display_name,
    v.provider_credential,
    v.is_individual,
    v.is_organization,

    -- Practice location
    v.practice_state,
    v.practice_city,
    v.practice_zip5,
    v.state_fips,

    -- Taxonomy / specialty (current version)
    v.primary_taxonomy_code,
    t.specialty_classification,
    t.specialty_specialization,
    t.specialty_display_name,
    t.specialty_grouping,
    v.taxonomy_count,

    -- Status
    v.is_active,
    v.enumeration_date,
    v.deactivation_date,

    -- SCD versioning
    v.dbt_valid_from,
    v.dbt_valid_to,
    v.dbt_scd_id,
    v.version_number,
    v.is_current,
    v.days_in_version,

    -- Change tracking
    v.previous_state,
    v.previous_taxonomy,
    case when v.previous_state is not null and v.previous_state != v.practice_state
        then true else false
    end as is_state_change,
    case when v.previous_taxonomy is not null and v.previous_taxonomy != v.primary_taxonomy_code
        then true else false
    end as is_taxonomy_change,

    -- Metadata
    v._snapshot_ts

from versioned v
left join taxonomy t on v.primary_taxonomy_code = t.taxonomy_code
