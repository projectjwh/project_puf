-- stg_cms__pos_facilities: Staging view over reference.ref_pos_facilities
-- Grain: one row per CCN (CMS Certification Number)
-- Value added: schema contract — isolates downstream from POS format changes

with source as (
    select * from {{ source('reference', 'ref_pos_facilities') }}
)

select
    ccn,
    facility_name,
    facility_type,
    facility_type_code,
    ownership_type,
    ownership_code,

    street_address,
    city,
    state,
    zip5,
    zip_full,
    county_code,
    phone,
    state_fips,

    bed_count,
    bed_count_total,

    certification_date,
    termination_date,
    is_active,
    medicare_participating,
    medicaid_participating,

    _loaded_at

from source
