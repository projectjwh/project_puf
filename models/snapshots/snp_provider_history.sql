{% snapshot snp_provider_history %}
{{
    config(
        target_schema='mart',
        unique_key='npi',
        strategy='check',
        check_cols=['primary_taxonomy_code', 'practice_state', 'practice_zip5', 'is_active', 'entity_type'],
        invalidate_hard_deletes=True,
    )
}}

-- snp_provider_history: SCD Type 2 snapshot of provider attributes
-- Grain: one row per NPI x validity period
-- Tracks changes to: taxonomy, practice state, ZIP, active status, entity type

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
    current_timestamp as _snapshot_ts
from {{ ref('int_providers') }}

{% endsnapshot %}
