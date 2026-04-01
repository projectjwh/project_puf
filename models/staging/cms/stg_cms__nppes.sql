-- stg_cms__nppes: Staging view over reference.ref_providers
-- Grain: one row per NPI
-- Value added: type-safe access layer, schema contract isolation
-- If CMS changes NPPES column names, ONLY this model + pipeline changes

with source as (
    select * from {{ source('reference', 'ref_providers') }}
)

select
    -- Identifiers
    npi,
    entity_type_code,
    entity_type,

    -- Names
    display_name,
    provider_last_name,
    provider_first_name,
    provider_middle_name,
    provider_credential,
    provider_organization_name,
    provider_gender_code,

    -- Practice address
    practice_address_line_1,
    practice_address_line_2,
    practice_city,
    practice_state,
    practice_zip5,
    practice_zip_full,
    practice_phone,
    practice_fax,
    state_fips,

    -- Taxonomy
    primary_taxonomy_code,
    taxonomy_count,

    -- Status
    enumeration_date,
    deactivation_date,
    reactivation_date,
    is_active,
    is_individual,
    is_organization,
    years_since_enumeration,

    -- Metadata
    _loaded_at,
    _snapshot_date

from source
