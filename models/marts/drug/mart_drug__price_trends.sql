-- mart_drug__price_trends: ASP quarterly price trends
-- Grain: HCPCS × quarter × year

{{ config(
    materialized='table',
    tags=['drug'],
) }}

with pricing as (
    select * from {{ ref('int_drug_pricing') }}
)

select
    hcpcs_code,
    short_description,
    payment_limit,
    dosage_form,
    quarter,
    year
from pricing
order by hcpcs_code, year, quarter
