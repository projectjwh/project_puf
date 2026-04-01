-- int_providers: Enriched provider dimension
-- Grain: one row per NPI
-- Value added over staging:
--   - Joins taxonomy description from ref_nucc_taxonomy
--   - Adds specialty grouping
--   - Standardizes gender display
--   - Adds geographic context (state name from FIPS)

with providers as (
    select * from {{ ref('stg_cms__nppes') }}
    where is_active = true
),

taxonomy as (
    select
        taxonomy_code,
        classification,
        specialization,
        display_name as taxonomy_display_name,
        grouping as taxonomy_grouping,
        is_individual as taxonomy_is_individual
    from {{ source('reference', 'ref_nucc_taxonomy') }}
),

states as (
    select
        state_fips,
        state_name,
        state_abbreviation,
        region,
        division
    from {{ source('reference', 'ref_state_fips') }}
)

select
    -- Provider identity
    p.npi,
    p.entity_type_code,
    p.entity_type,
    p.display_name,
    p.provider_last_name,
    p.provider_first_name,
    p.provider_credential,
    p.provider_organization_name,

    -- Gender (standardized)
    case p.provider_gender_code
        when 'M' then 'Male'
        when 'F' then 'Female'
        else 'Unknown'
    end as gender,

    -- Practice location
    p.practice_address_line_1,
    p.practice_city,
    p.practice_state,
    p.practice_zip5,
    p.state_fips,
    s.state_name,
    s.region as census_region,
    s.division as census_division,

    -- Taxonomy / specialty
    p.primary_taxonomy_code,
    t.classification as specialty_classification,
    t.specialization as specialty_specialization,
    t.taxonomy_display_name as specialty_display_name,
    t.taxonomy_grouping as specialty_grouping,
    p.taxonomy_count,

    -- Flags
    p.is_active,
    p.is_individual,
    p.is_organization,

    -- Tenure
    p.enumeration_date,
    p.years_since_enumeration,

    -- Metadata
    p._loaded_at

from providers p
left join taxonomy t on p.primary_taxonomy_code = t.taxonomy_code
left join states s on p.state_fips = s.state_fips
