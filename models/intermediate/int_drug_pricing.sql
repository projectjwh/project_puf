-- int_drug_pricing: ASP pricing with NDC crosswalk
-- Grain: HCPCS × quarter × year
-- Value added: Links ASP to NDC via RxNorm for cross-dataset drug analysis

{{ config(
    materialized='table',
    tags=['drug'],
) }}

select
    asp.hcpcs_code,
    asp.short_description,
    asp.payment_limit,
    asp.dosage_form,
    asp.quarter,
    asp.year
from {{ source('reference_tier2', 'ref_asp_pricing') }} asp
