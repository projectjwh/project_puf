-- stg_cms__geographic_variation: Staging view over Geographic Variation data
-- Grain: bene_geo_lvl × state/county_fips × data_year
-- Value added: type-safe access layer, schema contract isolation

{{ config(
    materialized='ephemeral',
    tags=['cms', 'staging', 'geographic'],
) }}

select
    -- Geography
    bene_geo_lvl,
    bene_geo_desc,
    bene_geo_cd,
    state_fips,
    county_fips,

    -- Beneficiary counts
    total_beneficiaries,
    total_beneficiaries_ffs,
    total_beneficiaries_ma,
    ma_participation_rate,

    -- Spending
    total_actual_costs,
    actual_per_capita_costs,
    standardized_per_capita_costs,

    -- Per-capita by service
    ip_per_capita_costs,
    op_per_capita_costs,
    snf_per_capita_costs,
    hha_per_capita_costs,
    hospice_per_capita_costs,
    partb_per_capita_costs,
    partd_per_capita_costs,
    dme_per_capita_costs,

    -- Utilization
    ip_covered_stays_per_1000,
    op_visits_per_1000,
    er_visits_per_1000,
    readmission_rate,
    ed_visit_rate,

    -- Year
    data_year,
    _loaded_at

from {{ source('staging', 'stg_cms__geographic_variation') }}
where data_year between {{ var('min_data_year') }} and {{ var('max_data_year') }}
