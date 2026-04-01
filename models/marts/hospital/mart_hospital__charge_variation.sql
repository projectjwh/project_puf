-- mart_hospital__charge_variation: Billed charges vs actual payments by DRG
-- Grain: CCN × DRG × data_year
-- Shows the spread between what hospitals bill and what they get paid

{{ config(
    materialized='table',
    tags=['hospital'],
) }}

with charges as (
    select * from {{ ref('stg_cms__charges') }}
)

select
    ccn,
    facility_name,
    provider_state,
    drg_code,
    drg_description,
    data_year,
    total_discharges,
    avg_covered_charges,
    avg_total_payments,
    avg_medicare_payments,
    total_covered_charges,
    total_payments,
    total_medicare_payments,
    -- Charge-to-payment ratio: how much hospitals bill vs. what they receive
    case
        when avg_total_payments > 0
        then round(avg_covered_charges::numeric / avg_total_payments, 2)
    end as charge_to_payment_ratio,
    -- Medicare share of total payments
    case
        when avg_total_payments > 0
        then round(avg_medicare_payments::numeric / avg_total_payments, 4)
    end as medicare_payment_share
from charges
