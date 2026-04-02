-- int_procedure_by_specialty: Procedure utilization broken out by provider specialty
-- Grain: hcpcs_code x specialty_classification x data_year
-- Value added over staging:
--   - Joins Part B service lines to int_providers for taxonomy classification
--   - Aggregates to procedure-specialty-year grain
--   - Enables "which specialties perform which procedures" analysis

{{ config(
    materialized='table',
    tags=['intermediate', 'procedure'],
) }}

with part_b as (
    select * from {{ ref('stg_cms__part_b_utilization') }}
),

providers as (
    select
        npi,
        specialty_classification
    from {{ ref('int_providers') }}
    where specialty_classification is not null
)

select
    pb.hcpcs_code,
    p.specialty_classification,
    pb.data_year,

    -- Volume
    sum(pb.number_of_services) as total_services,
    sum(pb.number_of_beneficiaries) as total_beneficiaries,
    count(distinct pb.rendering_npi) as provider_count,

    -- Payment totals (using pipeline-derived totals, NOT averages)
    sum(pb.total_medicare_payment) as total_medicare_payment,
    sum(pb.total_submitted_charge) as total_submitted_charge,

    -- Per-service average (re-derived from proper totals)
    case
        when sum(pb.number_of_services) > 0
        then round(sum(pb.total_medicare_payment)::numeric / sum(pb.number_of_services), 2)
    end as avg_payment_per_service

from part_b pb
inner join providers p on pb.rendering_npi = p.npi
group by pb.hcpcs_code, p.specialty_classification, pb.data_year
