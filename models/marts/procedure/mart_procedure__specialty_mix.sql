-- mart_procedure__specialty_mix: Specialty mix for each procedure
-- Grain: hcpcs_code x specialty_classification x data_year
-- Value added over intermediate:
--   - Computes specialty share of each procedure's total volume
--   - Ranks specialties within each procedure
--   - Pre-computed for API response shape
--   - Indexed for HCPCS lookup and specialty filtering

{{ config(
    materialized='table',
    tags=['procedure', 'mart', 'api'],
    indexes=[
        {'columns': ['hcpcs_code', 'data_year']},
        {'columns': ['specialty_classification']},
    ],
) }}

with specialty_procedures as (
    select * from {{ ref('int_procedure_by_specialty') }}
),

-- Total services per procedure-year for share calculation
procedure_totals as (
    select
        hcpcs_code,
        data_year,
        sum(total_services) as procedure_total_services,
        sum(total_medicare_payment) as procedure_total_payment
    from specialty_procedures
    group by hcpcs_code, data_year
),

-- HCPCS descriptions from the utilization intermediate
procedure_desc as (
    select
        hcpcs_code,
        hcpcs_description,
        data_year
    from {{ ref('int_procedure_utilization') }}
)

select
    sp.hcpcs_code,
    pd.hcpcs_description,
    sp.specialty_classification,
    sp.data_year,

    -- Volume
    sp.total_services,
    sp.total_beneficiaries,
    sp.provider_count,

    -- Payment
    sp.total_medicare_payment,
    sp.avg_payment_per_service,

    -- Share of procedure total
    case
        when pt.procedure_total_services > 0
        then round(sp.total_services::numeric / pt.procedure_total_services * 100, 2)
    end as services_share_pct,

    case
        when pt.procedure_total_payment > 0
        then round(sp.total_medicare_payment::numeric / pt.procedure_total_payment * 100, 2)
    end as payment_share_pct,

    -- Rank within procedure by volume
    row_number() over (
        partition by sp.hcpcs_code, sp.data_year
        order by sp.total_services desc
    ) as specialty_rank

from specialty_procedures sp
inner join procedure_totals pt
    on sp.hcpcs_code = pt.hcpcs_code
    and sp.data_year = pt.data_year
left join procedure_desc pd
    on sp.hcpcs_code = pd.hcpcs_code
    and sp.data_year = pd.data_year
