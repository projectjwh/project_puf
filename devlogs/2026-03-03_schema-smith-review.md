# Schema Smith Review: MVP Tier 1 Data Models

> **Agent**: Schema Smith | **Date**: 2026-03-03 | **Status**: APPROVED
> **Scope**: 4 MVP Tier 1 sources — NPPES, Part B Utilization, Part D Prescribers, Geographic Variation
> **Target Stack**: PostgreSQL (OLTP), DuckDB (OLAP), dbt-core (transforms)

---

## Table of Contents

1. [NPPES Provider Registry](#1-nppes-provider-registry)
2. [Medicare Part B Utilization](#2-medicare-part-b-utilization)
3. [Medicare Part D Prescribers](#3-medicare-part-d-prescribers)
4. [Medicare Geographic Variation](#4-medicare-geographic-variation)
5. [Cross-Source Models](#cross-source-models)
6. [SCD Strategy](#scd-strategy)
7. [dbt Project Structure](#dbt-project-structure)
8. [Overall Verdict](#overall-verdict)

---

# 1. NPPES Provider Registry

## Source Summary

- **Source**: NPPES NPI Registry (CMS) — bulk CSV download
- **Raw columns**: ~330 (many are repeated taxonomy/identifier slots 1-15 and 1-50)
- **Estimated rows**: ~8 million NPI records total (current + deactivated)
- **Update frequency**: Monthly bulk download, weekly incremental updates
- **Role in MVP**: Universal provider identity hub. Loaded first; every NPI join depends on it.

## Grain Definition

- **Staging grain**: One row per NPI (mirrors the source file — one record per enumerated provider)
- **Intermediate grain**: One row per NPI (cleaned, with taxonomy unpivoted into a separate model)
- **Mart grain(s)**:
  - `ref_providers`: One row per NPI (master provider dimension)
  - `ref_provider_taxonomies`: One row per NPI + taxonomy_code combination (unpivoted from 15 taxonomy slots)

## Entity-Relationship Map

NPPES is the **identity hub** of the entire data model. It contains:

- **Provider entities** (Type 1 = Individual, Type 2 = Organization) identified by NPI
- **Taxonomy classifications** (up to 15 per NPI) linking to the NUCC taxonomy standard
- **Practice location addresses** linking providers to geographies
- **Enumeration lifecycle** (enumeration date, deactivation, reactivation)

Relationships:
- `NPI` is the universal join key to Part B (`Rndrng_NPI`), Part D (`Prscrbr_NPI`), and all provider-level CMS datasets
- Practice location ZIP/state links contextually to Geographic Variation via FIPS codes
- `PAC_ID` links to Physician Compare / PECOS for group practice affiliations (future Tier 2)

## Model Layers

### Staging: `stg_cms__nppes`

One row per NPI. Direct 1:1 mapping from source with type casting and column renaming only.

| Column | Source Column | Type | Notes |
|--------|-------------|------|-------|
| `npi` | `NPI` | VARCHAR(10) | Primary key. 10-digit; stored as string (leading-zero safe) |
| `entity_type_code` | `Entity_Type_Code` | VARCHAR(1) | '1' = Individual, '2' = Organization |
| `provider_organization_name` | `Provider_Organization_Name` | VARCHAR(300) | Populated for Type 2 only |
| `provider_last_name` | `Provider_Last_Name` | VARCHAR(150) | Populated for Type 1 only |
| `provider_first_name` | `Provider_First_Name` | VARCHAR(100) | Populated for Type 1 only |
| `provider_middle_name` | `Provider_Middle_Name` | VARCHAR(100) | Nullable |
| `provider_name_prefix` | `Provider_Name_Prefix_Text` | VARCHAR(20) | Nullable |
| `provider_name_suffix` | `Provider_Name_Suffix_Text` | VARCHAR(20) | Nullable |
| `provider_credential` | `Provider_Credential_Text` | VARCHAR(50) | Free-text credentials (MD, DO, NP, etc.) |
| `provider_gender_code` | `Provider_Gender_Code` | VARCHAR(1) | 'M', 'F', or blank |
| `practice_address_line_1` | `Provider_First_Line_Business_Practice_Location_Address` | VARCHAR(300) | Primary practice address |
| `practice_address_line_2` | `Provider_Second_Line_Business_Practice_Location_Address` | VARCHAR(300) | Nullable |
| `practice_city_name` | `Provider_Business_Practice_Location_Address_City_Name` | VARCHAR(200) | |
| `practice_state_code` | `Provider_Business_Practice_Location_Address_State_Name` | VARCHAR(2) | State abbreviation |
| `practice_postal_code` | `Provider_Business_Practice_Location_Address_Postal_Code` | VARCHAR(20) | ZIP+4 or ZIP5 |
| `practice_country_code` | `Provider_Business_Practice_Location_Address_Country_Code` | VARCHAR(2) | 'US' for domestic |
| `practice_phone_number` | `Provider_Business_Practice_Location_Address_Telephone_Number` | VARCHAR(20) | |
| `practice_fax_number` | `Provider_Business_Practice_Location_Address_Fax_Number` | VARCHAR(20) | |
| `mailing_address_line_1` | `Provider_First_Line_Business_Mailing_Address` | VARCHAR(300) | |
| `mailing_address_line_2` | `Provider_Second_Line_Business_Mailing_Address` | VARCHAR(300) | |
| `mailing_city_name` | `Provider_Business_Mailing_Address_City_Name` | VARCHAR(200) | |
| `mailing_state_code` | `Provider_Business_Mailing_Address_State_Name` | VARCHAR(2) | |
| `mailing_postal_code` | `Provider_Business_Mailing_Address_Postal_Code` | VARCHAR(20) | |
| `mailing_country_code` | `Provider_Business_Mailing_Address_Country_Code` | VARCHAR(2) | |
| `mailing_phone_number` | `Provider_Business_Mailing_Address_Telephone_Number` | VARCHAR(20) | |
| `mailing_fax_number` | `Provider_Business_Mailing_Address_Fax_Number` | VARCHAR(20) | |
| `enumeration_date` | `Provider_Enumeration_Date` | DATE | When NPI was first assigned |
| `last_update_date` | `Last_Update_Date` | DATE | Most recent NPPES record update |
| `deactivation_reason_code` | `NPI_Deactivation_Reason_Code` | VARCHAR(2) | Nullable; indicates why NPI was deactivated |
| `deactivation_date` | `NPI_Deactivation_Date` | DATE | Nullable; NULL = active NPI |
| `reactivation_date` | `NPI_Reactivation_Date` | DATE | Nullable |
| `taxonomy_code_1` | `Healthcare_Provider_Taxonomy_Code_1` | VARCHAR(10) | Primary taxonomy slot |
| `taxonomy_primary_switch_1` | `Healthcare_Provider_Primary_Taxonomy_Switch_1` | VARCHAR(1) | 'Y' = primary taxonomy |
| `taxonomy_code_2` | `Healthcare_Provider_Taxonomy_Code_2` | VARCHAR(10) | |
| `taxonomy_primary_switch_2` | `Healthcare_Provider_Primary_Taxonomy_Switch_2` | VARCHAR(1) | |
| `taxonomy_code_3` through `taxonomy_code_15` | `Healthcare_Provider_Taxonomy_Code_3` through `_15` | VARCHAR(10) | Slots 3-15; most are NULL |
| `taxonomy_primary_switch_3` through `taxonomy_primary_switch_15` | Corresponding `_Primary_Taxonomy_Switch_*` | VARCHAR(1) | |
| `authorized_official_last_name` | `Authorized_Official_Last_Name` | VARCHAR(150) | For Type 2 orgs |
| `authorized_official_first_name` | `Authorized_Official_First_Name` | VARCHAR(100) | |
| `authorized_official_title` | `Authorized_Official_Title_or_Position` | VARCHAR(100) | |
| `authorized_official_phone` | `Authorized_Official_Telephone_Number` | VARCHAR(20) | |
| `is_sole_proprietor_flag` | `Is_Sole_Proprietor` | VARCHAR(1) | 'X' = yes, blank = no |
| `is_organization_subpart_flag` | `Is_Organization_Subpart` | VARCHAR(1) | 'X' = yes |
| `parent_organization_lbn` | `Parent_Organization_LBN` | VARCHAR(300) | Legal business name of parent org |
| `parent_organization_tin` | `Parent_Organization_TIN` | VARCHAR(9) | May be masked in PUF |
| `_loaded_at` | — | TIMESTAMP | dbt metadata: when row was loaded |

> **Note on omitted columns**: The 50 `Other_Provider_Identifier_*` slots and their type/state companions (~150 columns) are omitted from MVP staging. These contain legacy IDs (UPIN, Medicaid, etc.) that are valuable but not required for Tier 1 joins. They will be added in a future expansion as `stg_cms__nppes_other_identifiers`.

### Staging (Supplementary): `stg_cms__nppes_taxonomies` (ephemeral/CTE in dbt)

Unpivots the 15 taxonomy slots into rows during the staging-to-intermediate transform. This is implemented as a CTE or ephemeral model, not a persisted table.

| Column | Type | Source | Notes |
|--------|------|--------|-------|
| `npi` | VARCHAR(10) | `stg_cms__nppes.npi` | FK to provider |
| `taxonomy_code` | VARCHAR(10) | Unpivoted from `taxonomy_code_1` through `_15` | NUCC taxonomy code |
| `is_primary_taxonomy_flag` | BOOLEAN | Derived from `taxonomy_primary_switch_N` = 'Y' | |
| `taxonomy_slot_number` | SMALLINT | Derived from unpivot position (1-15) | |

### Intermediate: `int_providers`

One row per NPI. Cleans, normalizes, and enriches the staging data.

| Column | Type | Source | Transform |
|--------|------|--------|-----------|
| `npi` | VARCHAR(10) | `stg_cms__nppes.npi` | Direct passthrough |
| `entity_type_code` | VARCHAR(1) | `stg_cms__nppes.entity_type_code` | Direct |
| `entity_type_name` | VARCHAR(12) | Derived | CASE: '1' -> 'Individual', '2' -> 'Organization' |
| `provider_display_name` | VARCHAR(300) | Derived | Type 1: `last_name, first_name credential`; Type 2: `organization_name` |
| `provider_organization_name` | VARCHAR(300) | `stg_cms__nppes.provider_organization_name` | TRIM, UPPER normalization |
| `provider_last_name` | VARCHAR(150) | `stg_cms__nppes.provider_last_name` | TRIM, UPPER |
| `provider_first_name` | VARCHAR(100) | `stg_cms__nppes.provider_first_name` | TRIM, UPPER |
| `provider_middle_name` | VARCHAR(100) | `stg_cms__nppes.provider_middle_name` | TRIM, UPPER |
| `provider_credential` | VARCHAR(50) | `stg_cms__nppes.provider_credential` | TRIM, normalized (e.g., 'M.D.' -> 'MD') |
| `provider_gender_code` | VARCHAR(1) | `stg_cms__nppes.provider_gender_code` | Direct |
| `primary_taxonomy_code` | VARCHAR(10) | `stg_cms__nppes_taxonomies` CTE | Filtered where `is_primary_taxonomy_flag = TRUE`; takes first if multiple |
| `taxonomy_count` | SMALLINT | `stg_cms__nppes_taxonomies` CTE | COUNT of non-null taxonomy codes per NPI |
| `practice_address_line_1` | VARCHAR(300) | `stg_cms__nppes.practice_address_line_1` | TRIM |
| `practice_address_line_2` | VARCHAR(300) | `stg_cms__nppes.practice_address_line_2` | TRIM |
| `practice_city_name` | VARCHAR(200) | `stg_cms__nppes.practice_city_name` | TRIM, UPPER |
| `practice_state_code` | VARCHAR(2) | `stg_cms__nppes.practice_state_code` | TRIM, UPPER |
| `practice_zip5` | VARCHAR(5) | Derived from `practice_postal_code` | LEFT(postal_code, 5) — extract 5-digit ZIP |
| `practice_zip_plus4` | VARCHAR(4) | Derived from `practice_postal_code` | Substring 6-9 if present, else NULL |
| `practice_country_code` | VARCHAR(2) | `stg_cms__nppes.practice_country_code` | Direct |
| `practice_phone_number` | VARCHAR(20) | `stg_cms__nppes.practice_phone_number` | Direct |
| `enumeration_date` | DATE | `stg_cms__nppes.enumeration_date` | Direct |
| `last_update_date` | DATE | `stg_cms__nppes.last_update_date` | Direct |
| `deactivation_date` | DATE | `stg_cms__nppes.deactivation_date` | Direct |
| `reactivation_date` | DATE | `stg_cms__nppes.reactivation_date` | Direct |
| `is_active_flag` | BOOLEAN | Derived | `deactivation_date IS NULL OR reactivation_date > deactivation_date` |
| `is_individual_flag` | BOOLEAN | Derived | `entity_type_code = '1'` |
| `is_organization_flag` | BOOLEAN | Derived | `entity_type_code = '2'` |
| `is_sole_proprietor_flag` | BOOLEAN | Derived | `stg_cms__nppes.is_sole_proprietor_flag = 'X'` |
| `years_since_enumeration` | SMALLINT | Derived | `EXTRACT(YEAR FROM CURRENT_DATE) - EXTRACT(YEAR FROM enumeration_date)` |

### Mart: `ref_providers`

Master provider dimension table. One row per NPI. Used as a lookup/join target by all provider-level marts.

| Column | Type | Aggregation | Notes |
|--------|------|------------|-------|
| `npi` | VARCHAR(10) | -- | Primary key |
| `entity_type_code` | VARCHAR(1) | -- | '1' or '2' |
| `entity_type_name` | VARCHAR(12) | -- | 'Individual' or 'Organization' |
| `provider_display_name` | VARCHAR(300) | -- | Human-readable display name |
| `provider_last_name` | VARCHAR(150) | -- | Individuals only |
| `provider_first_name` | VARCHAR(100) | -- | Individuals only |
| `provider_credential` | VARCHAR(50) | -- | Normalized credential text |
| `provider_gender_code` | VARCHAR(1) | -- | 'M', 'F', or NULL |
| `primary_taxonomy_code` | VARCHAR(10) | -- | Self-reported primary NUCC taxonomy |
| `taxonomy_count` | SMALLINT | -- | Number of taxonomy codes on file |
| `practice_city_name` | VARCHAR(200) | -- | |
| `practice_state_code` | VARCHAR(2) | -- | |
| `practice_zip5` | VARCHAR(5) | -- | |
| `practice_country_code` | VARCHAR(2) | -- | |
| `enumeration_date` | DATE | -- | |
| `is_active_flag` | BOOLEAN | -- | |
| `is_individual_flag` | BOOLEAN | -- | |
| `is_organization_flag` | BOOLEAN | -- | |
| `years_since_enumeration` | SMALLINT | -- | |

### Mart: `ref_provider_taxonomies`

Unpivoted taxonomy dimension. One row per NPI + taxonomy code.

| Column | Type | Aggregation | Notes |
|--------|------|------------|-------|
| `npi` | VARCHAR(10) | -- | FK to `ref_providers` |
| `taxonomy_code` | VARCHAR(10) | -- | NUCC taxonomy code |
| `is_primary_taxonomy_flag` | BOOLEAN | -- | |
| `taxonomy_slot_number` | SMALLINT | -- | Position 1-15 from source |

## Keys & Indexes

| Model | Primary Key | Indexes | Foreign Keys |
|-------|------------|---------|--------------|
| `stg_cms__nppes` | `npi` | `entity_type_code`, `practice_state_code` | None (source mirror) |
| `int_providers` | `npi` | `practice_state_code`, `practice_zip5`, `primary_taxonomy_code`, `is_active_flag` | None |
| `ref_providers` | `npi` | `practice_state_code`, `practice_zip5`, `primary_taxonomy_code`, `entity_type_code`, `is_active_flag` | None (this is the hub) |
| `ref_provider_taxonomies` | `npi` + `taxonomy_code` | `taxonomy_code`, `is_primary_taxonomy_flag` | `npi` -> `ref_providers.npi` |

## Evaluation

| Criterion | Verdict | Notes |
|-----------|---------|-------|
| Grain clearly defined | **PASS** | One row per NPI at every layer; taxonomy unpivoted into separate model |
| Naming conventions followed | **PASS** | `stg_cms__nppes`, `int_providers`, `ref_providers`; columns use `{descriptor}_{type}` pattern |
| Types appropriate | **PASS** | NPI as VARCHAR(10), dates as DATE, flags as BOOLEAN |
| No mixed concerns per model | **PASS** | Staging mirrors source; intermediate cleans/derives; mart is dimensional |
| Relationships explicit | **PASS** | NPI is documented as universal join key; taxonomy FK defined |
| Codes stored as VARCHAR | **PASS** | NPI VARCHAR(10), taxonomy_code VARCHAR(10) |
| Money as DECIMAL | **PASS** | N/A — no monetary fields in NPPES |
| Healthcare domain patterns used | **PASS** | Entity type codes, NUCC taxonomy, enumeration lifecycle all modeled |
| Scalable at projected volume | **PASS** | 8M rows is modest; indexes on state/zip/taxonomy support query patterns |
| Lineage traceable raw->mart | **PASS** | Clear lineage: NPPES CSV -> stg_cms__nppes -> int_providers -> ref_providers |

## Verdict: APPROVED

---

# 2. Medicare Part B Utilization

## Source Summary

- **Source**: Medicare Provider Utilization and Payment Data: Physician and Other Practitioners (CMS)
- **Raw columns**: ~30 per annual file
- **Estimated rows**: ~10 million per year (provider-service-place_of_service grain)
- **Update frequency**: Annual (18-24 month lag)
- **Current coverage**: 2013-2022 (latest year needs verification)

## Grain Definition

- **Staging grain**: One row per rendering NPI + HCPCS code + place of service + data year
- **Intermediate grain**: One row per rendering NPI + HCPCS code + place of service + data year (cleaned, enriched with provider dimension join)
- **Mart grain(s)**:
  - `mart_provider__by_specialty`: One row per provider type (specialty) + data year
  - `mart_provider__practice_profile`: One row per NPI + data year (aggregated across all services)
  - `mart_geographic__by_state`: One row per state + data year (aggregated Part B + Part D spending)

## Entity-Relationship Map

Part B Utilization is a **fact table** at the provider-service level:

- **Provider** (identified by `Rndrng_NPI`) -> joins to `ref_providers` via NPI
- **Service** (identified by `HCPCS_Cd`) -> joins to `ref_hcpcs_codes` for code descriptions
- **Geography** (identified by `Rndrng_Prvdr_State_FIPS`) -> joins to `ref_geographies` and `Geographic Variation`
- **Place of Service** ('F' = Facility, 'O' = Office) -> embedded dimension

This is a many-to-many between providers and services: a provider bills many HCPCS codes, and a HCPCS code is billed by many providers.

## Model Layers

### Staging: `stg_cms__part_b_utilization`

One row per NPI + HCPCS + place of service + data year. Direct type-cast and rename from source.

| Column | Source Column | Type | Notes |
|--------|-------------|------|-------|
| `rendering_npi` | `Rndrng_NPI` | VARCHAR(10) | Rendering provider NPI |
| `rendering_provider_last_org_name` | `Rndrng_Prvdr_Last_Org_Name` | VARCHAR(300) | Last name (individual) or org name |
| `rendering_provider_first_name` | `Rndrng_Prvdr_First_Name` | VARCHAR(100) | NULL for organizations |
| `rendering_provider_credential` | `Rndrng_Prvdr_Crdntls` | VARCHAR(50) | Free-text credential |
| `rendering_provider_gender_code` | `Rndrng_Prvdr_Gndr` | VARCHAR(1) | 'M', 'F', or blank |
| `rendering_provider_entity_code` | `Rndrng_Prvdr_Ent_Cd` | VARCHAR(1) | 'I' = Individual, 'O' = Organization |
| `rendering_provider_street_1` | `Rndrng_Prvdr_St1` | VARCHAR(300) | |
| `rendering_provider_street_2` | `Rndrng_Prvdr_St2` | VARCHAR(300) | |
| `rendering_provider_city_name` | `Rndrng_Prvdr_City` | VARCHAR(200) | |
| `rendering_provider_state_code` | `Rndrng_Prvdr_State_Abrvtn` | VARCHAR(2) | State abbreviation |
| `rendering_provider_state_fips` | `Rndrng_Prvdr_State_FIPS` | VARCHAR(2) | 2-digit FIPS; VARCHAR for leading zero |
| `rendering_provider_zip5` | `Rndrng_Prvdr_Zip5` | VARCHAR(5) | |
| `rendering_provider_ruca_code` | `Rndrng_Prvdr_RUCA` | VARCHAR(10) | Rural-Urban Commuting Area code |
| `rendering_provider_type` | `Rndrng_Prvdr_Type` | VARCHAR(100) | CMS specialty description |
| `hcpcs_code` | `HCPCS_Cd` | VARCHAR(5) | HCPCS/CPT procedure code — always VARCHAR |
| `hcpcs_description` | `HCPCS_Desc` | VARCHAR(500) | |
| `hcpcs_drug_indicator_flag` | `HCPCS_Drug_Ind` | VARCHAR(1) | 'Y' = drug code |
| `place_of_service_code` | `Place_Of_Srvc` | VARCHAR(1) | 'F' = Facility, 'O' = Office (non-facility) |
| `beneficiary_count` | `Tot_Benes` | INTEGER | Total unique beneficiaries |
| `service_count` | `Tot_Srvcs` | INTEGER | Total services (line items) |
| `beneficiary_day_service_count` | `Tot_Bene_Day_Srvcs` | INTEGER | Unique beneficiary-day-services |
| `avg_submitted_charge_amount` | `Avg_Sbmtd_Chrg` | DECIMAL(18,2) | Average submitted charge |
| `avg_medicare_allowed_amount` | `Avg_Mdcr_Alowd_Amt` | DECIMAL(18,2) | Average Medicare allowed amount |
| `avg_medicare_payment_amount` | `Avg_Mdcr_Pymt_Amt` | DECIMAL(18,2) | Average Medicare payment |
| `avg_medicare_standardized_amount` | `Avg_Mdcr_Stdzd_Amt` | DECIMAL(18,2) | Average standardized payment (geo-adjusted) |
| `data_year` | Derived from filename or metadata | SMALLINT | Year of service data |
| `_loaded_at` | — | TIMESTAMP | dbt metadata |

### Intermediate: `int_provider_services`

One row per NPI + HCPCS + place of service + data year. Derives total payment columns (avg * count), adds provider dimension attributes via join to `int_providers`.

| Column | Type | Source | Transform |
|--------|------|--------|-----------|
| `rendering_npi` | VARCHAR(10) | `stg_cms__part_b_utilization.rendering_npi` | Direct |
| `hcpcs_code` | VARCHAR(5) | `stg_cms__part_b_utilization.hcpcs_code` | Direct |
| `hcpcs_description` | VARCHAR(500) | `stg_cms__part_b_utilization.hcpcs_description` | Direct |
| `place_of_service_code` | VARCHAR(1) | `stg_cms__part_b_utilization.place_of_service_code` | Direct |
| `place_of_service_name` | VARCHAR(20) | Derived | CASE: 'F' -> 'Facility', 'O' -> 'Office' |
| `data_year` | SMALLINT | `stg_cms__part_b_utilization.data_year` | Direct |
| `is_drug_service_flag` | BOOLEAN | Derived | `hcpcs_drug_indicator_flag = 'Y'` |
| `is_individual_provider_flag` | BOOLEAN | Derived | `rendering_provider_entity_code = 'I'` |
| `rendering_provider_type` | VARCHAR(100) | `stg_cms__part_b_utilization.rendering_provider_type` | Direct |
| `rendering_provider_state_code` | VARCHAR(2) | `stg_cms__part_b_utilization.rendering_provider_state_code` | Direct |
| `rendering_provider_state_fips` | VARCHAR(2) | `stg_cms__part_b_utilization.rendering_provider_state_fips` | Direct |
| `rendering_provider_zip5` | VARCHAR(5) | `stg_cms__part_b_utilization.rendering_provider_zip5` | Direct |
| `rendering_provider_ruca_code` | VARCHAR(10) | `stg_cms__part_b_utilization.rendering_provider_ruca_code` | Direct |
| `beneficiary_count` | INTEGER | `stg_cms__part_b_utilization.beneficiary_count` | Direct |
| `service_count` | INTEGER | `stg_cms__part_b_utilization.service_count` | Direct |
| `beneficiary_day_service_count` | INTEGER | `stg_cms__part_b_utilization.beneficiary_day_service_count` | Direct |
| `avg_submitted_charge_amount` | DECIMAL(18,2) | `stg_cms__part_b_utilization.avg_submitted_charge_amount` | Direct |
| `avg_medicare_allowed_amount` | DECIMAL(18,2) | `stg_cms__part_b_utilization.avg_medicare_allowed_amount` | Direct |
| `avg_medicare_payment_amount` | DECIMAL(18,2) | `stg_cms__part_b_utilization.avg_medicare_payment_amount` | Direct |
| `avg_medicare_standardized_amount` | DECIMAL(18,2) | `stg_cms__part_b_utilization.avg_medicare_standardized_amount` | Direct |
| `total_submitted_charge_amount` | DECIMAL(18,2) | Derived | `avg_submitted_charge_amount * service_count` |
| `total_medicare_allowed_amount` | DECIMAL(18,2) | Derived | `avg_medicare_allowed_amount * service_count` |
| `total_medicare_payment_amount` | DECIMAL(18,2) | Derived | `avg_medicare_payment_amount * service_count` |
| `total_medicare_standardized_amount` | DECIMAL(18,2) | Derived | `avg_medicare_standardized_amount * service_count` |
| `avg_services_per_beneficiary` | DECIMAL(7,4) | Derived | `service_count / NULLIF(beneficiary_count, 0)` |

### Mart: `mart_provider__by_specialty`

One row per provider specialty + data year. Aggregates across all providers of the same type.

| Column | Type | Aggregation | Notes |
|--------|------|------------|-------|
| `rendering_provider_type` | VARCHAR(100) | -- | Group key: CMS specialty |
| `data_year` | SMALLINT | -- | Group key |
| `provider_count` | INTEGER | COUNT(DISTINCT `rendering_npi`) | Unique providers in specialty |
| `total_beneficiary_count` | BIGINT | SUM(`beneficiary_count`) | Not unique beneficiaries across providers |
| `total_service_count` | BIGINT | SUM(`service_count`) | |
| `total_medicare_payment_amount` | DECIMAL(18,2) | SUM(`total_medicare_payment_amount`) | |
| `total_medicare_standardized_amount` | DECIMAL(18,2) | SUM(`total_medicare_standardized_amount`) | |
| `avg_payment_per_service_amount` | DECIMAL(18,2) | Weighted avg | `total_medicare_payment / total_service_count` |
| `avg_services_per_provider_count` | DECIMAL(10,2) | AVG | `total_service_count / provider_count` |
| `avg_beneficiaries_per_provider_count` | DECIMAL(10,2) | AVG | `total_beneficiary_count / provider_count` |
| `distinct_hcpcs_code_count` | INTEGER | COUNT(DISTINCT `hcpcs_code`) | Breadth of coding |
| `drug_service_rate` | DECIMAL(7,4) | Ratio | Fraction of services that are drug codes |

### Mart: `mart_provider__practice_profile`

One row per NPI + data year. Aggregates all services per provider into a single practice profile. (Cross-source: will later be enriched with Part D data.)

| Column | Type | Aggregation | Notes |
|--------|------|------------|-------|
| `rendering_npi` | VARCHAR(10) | -- | Group key |
| `data_year` | SMALLINT | -- | Group key |
| `provider_display_name` | VARCHAR(300) | -- | From `ref_providers` join |
| `primary_taxonomy_code` | VARCHAR(10) | -- | From `ref_providers` join |
| `rendering_provider_type` | VARCHAR(100) | -- | CMS specialty from Part B data |
| `rendering_provider_state_code` | VARCHAR(2) | -- | |
| `rendering_provider_zip5` | VARCHAR(5) | -- | |
| `total_beneficiary_count` | INTEGER | SUM(`beneficiary_count`) | Across all HCPCS codes |
| `total_service_count` | BIGINT | SUM(`service_count`) | |
| `total_medicare_payment_amount` | DECIMAL(18,2) | SUM(`total_medicare_payment_amount`) | |
| `total_medicare_standardized_amount` | DECIMAL(18,2) | SUM(`total_medicare_standardized_amount`) | |
| `total_submitted_charge_amount` | DECIMAL(18,2) | SUM(`total_submitted_charge_amount`) | |
| `distinct_hcpcs_code_count` | INTEGER | COUNT(DISTINCT `hcpcs_code`) | Code diversity |
| `distinct_beneficiary_day_count` | BIGINT | SUM(`beneficiary_day_service_count`) | |
| `facility_service_rate` | DECIMAL(7,4) | Ratio | Services at facility vs. total |
| `drug_service_rate` | DECIMAL(7,4) | Ratio | Drug services vs. total |
| `avg_payment_per_service_amount` | DECIMAL(18,2) | Weighted avg | |
| `avg_services_per_beneficiary_count` | DECIMAL(7,4) | Ratio | Intensity measure |

## Keys & Indexes

| Model | Primary Key | Indexes | Foreign Keys |
|-------|------------|---------|--------------|
| `stg_cms__part_b_utilization` | `rendering_npi` + `hcpcs_code` + `place_of_service_code` + `data_year` | `rendering_npi`, `hcpcs_code`, `rendering_provider_state_fips`, `data_year` | None (source mirror) |
| `int_provider_services` | `rendering_npi` + `hcpcs_code` + `place_of_service_code` + `data_year` | `rendering_npi`, `hcpcs_code`, `rendering_provider_state_fips`, `rendering_provider_type`, `data_year` | `rendering_npi` -> `ref_providers.npi` |
| `mart_provider__by_specialty` | `rendering_provider_type` + `data_year` | `data_year` | None |
| `mart_provider__practice_profile` | `rendering_npi` + `data_year` | `rendering_npi`, `rendering_provider_state_code`, `rendering_provider_type`, `data_year` | `rendering_npi` -> `ref_providers.npi` |

## Evaluation

| Criterion | Verdict | Notes |
|-----------|---------|-------|
| Grain clearly defined | **PASS** | Staging: NPI+HCPCS+POS+year. Int: same. Mart: aggregated per specialty or per provider per year. |
| Naming conventions followed | **PASS** | `stg_cms__part_b_utilization`, `int_provider_services`, `mart_provider__*` |
| Types appropriate | **PASS** | NPI/HCPCS as VARCHAR, money as DECIMAL(18,2), counts as INTEGER/BIGINT, rates as DECIMAL(7,4) |
| No mixed concerns per model | **PASS** | Staging = source mirror; int = derived fields (totals); mart = aggregated analytics |
| Relationships explicit | **PASS** | NPI joins to ref_providers; HCPCS joins to ref_hcpcs_codes; State FIPS joins to ref_geographies |
| Codes stored as VARCHAR | **PASS** | HCPCS VARCHAR(5), NPI VARCHAR(10), FIPS VARCHAR(2), RUCA VARCHAR(10) |
| Money as DECIMAL | **PASS** | All `_amount` columns are DECIMAL(18,2) |
| Healthcare domain patterns used | **PASS** | Place of service, entity type, CMS specialty, HCPCS drug indicator, standardized amounts all modeled |
| Scalable at projected volume | **PASS** | ~10M rows/year is well within PostgreSQL/DuckDB capacity; composite indexes on common query patterns |
| Lineage traceable raw->mart | **PASS** | CSV -> stg_cms__part_b_utilization -> int_provider_services -> mart_provider__practice_profile / mart_provider__by_specialty |

## Verdict: APPROVED

---

# 3. Medicare Part D Prescribers

## Source Summary

- **Source**: Medicare Part D Prescribers — by Provider and Drug (CMS)
- **Raw columns**: ~30 per annual file
- **Estimated rows**: ~25 million per year (provider-drug grain)
- **Update frequency**: Annual (18-24 month lag)
- **Current coverage**: 2013-2022 (latest year needs verification)

## Grain Definition

- **Staging grain**: One row per prescriber NPI + brand name + generic name + data year
- **Intermediate grain**: One row per prescriber NPI + brand name + generic name + data year (cleaned, enriched with derived cost and utilization fields)
- **Mart grain(s)**:
  - `mart_provider__practice_profile`: One row per NPI + data year (Part D columns added to combined profile)
  - `mart_provider__prescribing_summary`: One row per NPI + data year (prescribing-specific aggregation)
  - `mart_geographic__by_state`: One row per state + data year (drug spending by geography)

## Entity-Relationship Map

Part D Prescribers is a **fact table** at the prescriber-drug level:

- **Prescriber** (identified by `Prscrbr_NPI`) -> joins to `ref_providers` via NPI
- **Drug** (identified by `Brnd_Name` + `Gnrc_Name`) -> future `ref_drugs` table (not yet built; drug name normalization is a known challenge)
- **Geography** (identified by `Prscrbr_State_FIPS`) -> joins to `ref_geographies` and Geographic Variation
- **Opioid classification** (identified by flag fields) -> embedded flags

The provider-drug grain is many-to-many: a prescriber writes for many drugs, and a drug is prescribed by many prescribers.

## Model Layers

### Staging: `stg_cms__part_d_prescribers`

One row per NPI + brand + generic + data year. Direct type-cast and rename.

| Column | Source Column | Type | Notes |
|--------|-------------|------|-------|
| `prescriber_npi` | `Prscrbr_NPI` | VARCHAR(10) | Prescriber NPI |
| `prescriber_last_org_name` | `Prscrbr_Last_Org_Name` | VARCHAR(300) | |
| `prescriber_first_name` | `Prscrbr_First_Name` | VARCHAR(100) | |
| `prescriber_credential` | `Prscrbr_Crdntls` | VARCHAR(50) | |
| `prescriber_gender_code` | `Prscrbr_Gndr` | VARCHAR(1) | |
| `prescriber_entity_code` | `Prscrbr_Ent_Cd` | VARCHAR(1) | 'I' or 'O' |
| `prescriber_street_1` | `Prscrbr_St1` | VARCHAR(300) | |
| `prescriber_street_2` | `Prscrbr_St2` | VARCHAR(300) | |
| `prescriber_city_name` | `Prscrbr_City` | VARCHAR(200) | |
| `prescriber_state_code` | `Prscrbr_State_Abrvtn` | VARCHAR(2) | |
| `prescriber_state_fips` | `Prscrbr_State_FIPS` | VARCHAR(2) | 2-digit FIPS as VARCHAR |
| `prescriber_zip5` | `Prscrbr_Zip5` | VARCHAR(5) | |
| `prescriber_ruca_code` | `Prscrbr_RUCA` | VARCHAR(10) | |
| `prescriber_type` | `Prscrbr_Type` | VARCHAR(100) | CMS specialty |
| `drug_brand_name` | `Brnd_Name` | VARCHAR(200) | Brand name of drug |
| `drug_generic_name` | `Gnrc_Name` | VARCHAR(200) | Generic/chemical name |
| `total_claim_count` | `Tot_Clms` | INTEGER | Total 30-day equivalent claims |
| `total_30day_fill_count` | `Tot_30day_Fills` | DECIMAL(10,2) | 30-day standardized fill equivalents |
| `total_beneficiary_count` | `Tot_Benes` | INTEGER | Unique beneficiaries |
| `total_day_supply_count` | `Tot_Day_Suply` | INTEGER | Total days of supply dispensed |
| `total_drug_cost_amount` | `Tot_Drug_Cst` | DECIMAL(18,2) | Total drug cost (ingredient + dispensing + tax) |
| `ge65_claim_count` | `GE65_Tot_Clms` | INTEGER | Claims for beneficiaries 65+ |
| `ge65_30day_fill_count` | `GE65_Tot_30day_Fills` | DECIMAL(10,2) | |
| `ge65_beneficiary_count` | `GE65_Tot_Benes` | INTEGER | |
| `ge65_day_supply_count` | `GE65_Tot_Day_Suply` | INTEGER | |
| `ge65_drug_cost_amount` | `GE65_Tot_Drug_Cst` | DECIMAL(18,2) | |
| `ge65_suppression_flag` | `GE65_Sprsn_Flag` | VARCHAR(1) | '#' = suppressed |
| `is_opioid_drug_flag` | `Opioid_Drug_Flag` | VARCHAR(1) | 'Y' = opioid |
| `is_long_acting_opioid_drug_flag` | `Opioid_LA_Drug_Flag` | VARCHAR(1) | 'Y' = long-acting opioid |
| `is_antibiotic_drug_flag` | `Antbtc_Drug_Flag` | VARCHAR(1) | 'Y' = antibiotic |
| `data_year` | Derived from filename or metadata | SMALLINT | |
| `_loaded_at` | — | TIMESTAMP | dbt metadata |

### Intermediate: `int_provider_prescriptions`

One row per NPI + brand + generic + data year. Cleans flags to booleans, derives cost-per-unit metrics, joins to provider dimension.

| Column | Type | Source | Transform |
|--------|------|--------|-----------|
| `prescriber_npi` | VARCHAR(10) | `stg_cms__part_d_prescribers.prescriber_npi` | Direct |
| `drug_brand_name` | VARCHAR(200) | `stg_cms__part_d_prescribers.drug_brand_name` | TRIM, UPPER |
| `drug_generic_name` | VARCHAR(200) | `stg_cms__part_d_prescribers.drug_generic_name` | TRIM, UPPER |
| `data_year` | SMALLINT | `stg_cms__part_d_prescribers.data_year` | Direct |
| `prescriber_type` | VARCHAR(100) | `stg_cms__part_d_prescribers.prescriber_type` | Direct |
| `prescriber_state_code` | VARCHAR(2) | `stg_cms__part_d_prescribers.prescriber_state_code` | Direct |
| `prescriber_state_fips` | VARCHAR(2) | `stg_cms__part_d_prescribers.prescriber_state_fips` | Direct |
| `prescriber_zip5` | VARCHAR(5) | `stg_cms__part_d_prescribers.prescriber_zip5` | Direct |
| `prescriber_ruca_code` | VARCHAR(10) | `stg_cms__part_d_prescribers.prescriber_ruca_code` | Direct |
| `is_individual_prescriber_flag` | BOOLEAN | Derived | `prescriber_entity_code = 'I'` |
| `is_opioid_drug_flag` | BOOLEAN | Derived | Source `is_opioid_drug_flag = 'Y'` |
| `is_long_acting_opioid_drug_flag` | BOOLEAN | Derived | Source `is_long_acting_opioid_drug_flag = 'Y'` |
| `is_antibiotic_drug_flag` | BOOLEAN | Derived | Source `is_antibiotic_drug_flag = 'Y'` |
| `total_claim_count` | INTEGER | Direct | |
| `total_30day_fill_count` | DECIMAL(10,2) | Direct | |
| `total_beneficiary_count` | INTEGER | Direct | |
| `total_day_supply_count` | INTEGER | Direct | |
| `total_drug_cost_amount` | DECIMAL(18,2) | Direct | |
| `ge65_claim_count` | INTEGER | Direct | |
| `ge65_beneficiary_count` | INTEGER | Direct | |
| `ge65_drug_cost_amount` | DECIMAL(18,2) | Direct | |
| `is_ge65_suppressed_flag` | BOOLEAN | Derived | `ge65_suppression_flag = '#'` |
| `cost_per_claim_amount` | DECIMAL(18,2) | Derived | `total_drug_cost_amount / NULLIF(total_claim_count, 0)` |
| `cost_per_day_supply_amount` | DECIMAL(18,2) | Derived | `total_drug_cost_amount / NULLIF(total_day_supply_count, 0)` |
| `cost_per_beneficiary_amount` | DECIMAL(18,2) | Derived | `total_drug_cost_amount / NULLIF(total_beneficiary_count, 0)` |
| `avg_day_supply_per_claim_count` | DECIMAL(7,4) | Derived | `total_day_supply_count / NULLIF(total_claim_count, 0)` |

### Mart: `mart_provider__prescribing_summary`

One row per prescriber NPI + data year. Aggregates all drugs per prescriber.

| Column | Type | Aggregation | Notes |
|--------|------|------------|-------|
| `prescriber_npi` | VARCHAR(10) | -- | Group key |
| `data_year` | SMALLINT | -- | Group key |
| `provider_display_name` | VARCHAR(300) | -- | From `ref_providers` join |
| `prescriber_type` | VARCHAR(100) | -- | CMS specialty |
| `prescriber_state_code` | VARCHAR(2) | -- | |
| `prescriber_zip5` | VARCHAR(5) | -- | |
| `total_claim_count` | BIGINT | SUM | Across all drugs |
| `total_30day_fill_count` | DECIMAL(18,2) | SUM | |
| `total_beneficiary_count` | INTEGER | SUM | Not unique across drugs |
| `total_day_supply_count` | BIGINT | SUM | |
| `total_drug_cost_amount` | DECIMAL(18,2) | SUM | |
| `distinct_drug_count` | INTEGER | COUNT(DISTINCT `drug_generic_name`) | Number of unique drugs prescribed |
| `distinct_brand_count` | INTEGER | COUNT(DISTINCT `drug_brand_name`) | |
| `opioid_claim_count` | BIGINT | SUM WHERE `is_opioid_drug_flag` | |
| `opioid_drug_cost_amount` | DECIMAL(18,2) | SUM WHERE `is_opioid_drug_flag` | |
| `opioid_beneficiary_count` | INTEGER | SUM WHERE `is_opioid_drug_flag` | |
| `long_acting_opioid_claim_count` | BIGINT | SUM WHERE `is_long_acting_opioid_drug_flag` | |
| `antibiotic_claim_count` | BIGINT | SUM WHERE `is_antibiotic_drug_flag` | |
| `antibiotic_drug_cost_amount` | DECIMAL(18,2) | SUM WHERE `is_antibiotic_drug_flag` | |
| `opioid_claim_rate` | DECIMAL(7,4) | Ratio | `opioid_claim_count / NULLIF(total_claim_count, 0)` |
| `antibiotic_claim_rate` | DECIMAL(7,4) | Ratio | `antibiotic_claim_count / NULLIF(total_claim_count, 0)` |
| `avg_cost_per_claim_amount` | DECIMAL(18,2) | Weighted avg | `total_drug_cost / total_claim_count` |
| `avg_cost_per_beneficiary_amount` | DECIMAL(18,2) | Weighted avg | `total_drug_cost / total_beneficiary_count` |

## Keys & Indexes

| Model | Primary Key | Indexes | Foreign Keys |
|-------|------------|---------|--------------|
| `stg_cms__part_d_prescribers` | `prescriber_npi` + `drug_brand_name` + `drug_generic_name` + `data_year` | `prescriber_npi`, `drug_generic_name`, `prescriber_state_fips`, `data_year` | None (source mirror) |
| `int_provider_prescriptions` | `prescriber_npi` + `drug_brand_name` + `drug_generic_name` + `data_year` | `prescriber_npi`, `drug_generic_name`, `prescriber_state_fips`, `data_year`, `is_opioid_drug_flag` | `prescriber_npi` -> `ref_providers.npi` |
| `mart_provider__prescribing_summary` | `prescriber_npi` + `data_year` | `prescriber_npi`, `prescriber_state_code`, `prescriber_type`, `data_year` | `prescriber_npi` -> `ref_providers.npi` |

## Evaluation

| Criterion | Verdict | Notes |
|-----------|---------|-------|
| Grain clearly defined | **PASS** | Staging/Int: NPI + brand + generic + year. Mart: NPI + year. |
| Naming conventions followed | **PASS** | `stg_cms__part_d_prescribers`, `int_provider_prescriptions`, `mart_provider__prescribing_summary` |
| Types appropriate | **PASS** | NPI as VARCHAR, cost as DECIMAL(18,2), counts as INTEGER/BIGINT, rates as DECIMAL(7,4) |
| No mixed concerns per model | **PASS** | Staging = source; int = derived cost-per-unit metrics; mart = provider-level aggregation |
| Relationships explicit | **PASS** | NPI joins to ref_providers; state FIPS joins to ref_geographies |
| Codes stored as VARCHAR | **PASS** | NPI VARCHAR(10), FIPS VARCHAR(2), RUCA VARCHAR(10) |
| Money as DECIMAL | **PASS** | All `_amount` columns DECIMAL(18,2) |
| Healthcare domain patterns used | **PASS** | Opioid/antibiotic flags, 30-day fill standardization, brand/generic distinction, ge65 demographics |
| Scalable at projected volume | **PASS** | ~25M rows/year is larger; composite indexes and materialized marts address query performance |
| Lineage traceable raw->mart | **PASS** | CSV -> stg -> int_provider_prescriptions -> mart_provider__prescribing_summary |

## Verdict: APPROVED

---

# 4. Medicare Geographic Variation

## Source Summary

- **Source**: Medicare Geographic Variation — by National, State, and County (CMS)
- **Raw columns**: ~60-80 per file (varies by level)
- **Estimated rows**: ~3,250 per year (1 national + ~50 state + ~3,200 county)
- **Update frequency**: Annual (18-24 month lag)
- **Current coverage**: 2007-2022 (latest year needs verification)

## Grain Definition

- **Staging grain**: One row per geographic level + state FIPS + county FIPS + data year
- **Intermediate grain**: One row per geographic level + state FIPS + county FIPS + data year (cleaned, with derived per-capita fields and flag columns)
- **Mart grain(s)**:
  - `ref_geographies`: One row per county FIPS (reference dimension)
  - `mart_geographic__spending_variation`: One row per geography + data year (cross-source: augmented with Part B + Part D aggregations)
  - `mart_geographic__by_state`: One row per state + data year (state-level summary combining geo variation with aggregated Part B/Part D)

## Entity-Relationship Map

Geographic Variation is a **reference/benchmark table** at the population level:

- **Geography** (National/State/County, identified by FIPS codes) -> joins to provider-level data via state FIPS
- **Beneficiary population** characteristics per geography
- **Spending benchmarks** per capita by service category
- **Utilization rates** per 1,000 beneficiaries

This is not a transactional fact table but a contextual dimension providing population-level denominators for interpreting provider-level data.

## Model Layers

### Staging: `stg_cms__geographic_variation`

One row per geographic level + FIPS + data year. Direct type-cast and rename.

| Column | Source Column | Type | Notes |
|--------|-------------|------|-------|
| `geographic_level` | `BENE_GEO_LVL` | VARCHAR(10) | 'National', 'State', or 'County' |
| `state_name` | `State` | VARCHAR(50) | Full state name |
| `state_fips` | `State_FIPS` | VARCHAR(2) | 2-digit FIPS; VARCHAR for leading zeros |
| `county_name` | `County` | VARCHAR(100) | Full county name (county-level rows only) |
| `county_fips` | `County_FIPS` | VARCHAR(5) | 5-digit FIPS (county-level rows only) |
| `ffs_beneficiary_count` | `Benes_FFS_Cnt` | INTEGER | FFS beneficiaries |
| `ma_beneficiary_count` | `Benes_MA_Cnt` | INTEGER | MA beneficiaries |
| `dual_eligible_beneficiary_count` | `Benes_Dual_Cnt` | INTEGER | Dual-eligible (Medicare + Medicaid) |
| `beneficiary_age_lt65_count` | `Benes_Age_LT65_Cnt` | INTEGER | Under 65 (disability-qualified) |
| `beneficiary_age_65_74_count` | `Benes_Age_65_74_Cnt` | INTEGER | |
| `beneficiary_age_75_84_count` | `Benes_Age_75_84_Cnt` | INTEGER | |
| `beneficiary_age_gt84_count` | `Benes_Age_GT84_Cnt` | INTEGER | |
| `avg_hcc_risk_score` | `Benes_Avg_HCC_Scr` | DECIMAL(7,4) | Average HCC risk score — critical confounder |
| `total_medicare_standardized_per_capita_amount` | `Tot_Mdcr_Stdzd_Pymt_PC` | DECIMAL(18,2) | Standardized per-capita spending |
| `total_medicare_actual_per_capita_amount` | `Tot_Mdcr_Pymt_PC` | DECIMAL(18,2) | Actual per-capita spending |
| `ip_medicare_per_capita_amount` | `IP_Mdcr_Pymt_PC` | DECIMAL(18,2) | Inpatient per-capita spending |
| `pac_medicare_per_capita_amount` | `PAC_Mdcr_Pymt_PC` | DECIMAL(18,2) | Post-acute care per-capita |
| `physician_medicare_per_capita_amount` | `Phys_Mdcr_Pymt_PC` | DECIMAL(18,2) | Physician services per-capita |
| `op_medicare_per_capita_amount` | `OP_Mdcr_Pymt_PC` | DECIMAL(18,2) | Outpatient per-capita |
| `hh_medicare_per_capita_amount` | `HH_Mdcr_Pymt_PC` | DECIMAL(18,2) | Home health per-capita |
| `hospice_medicare_per_capita_amount` | `Hospice_Mdcr_Pymt_PC` | DECIMAL(18,2) | Hospice per-capita |
| `dme_medicare_per_capita_amount` | `DME_Mdcr_Pymt_PC` | DECIMAL(18,2) | DME per-capita |
| `partd_medicare_per_capita_amount` | `PartD_Mdcr_Pymt_PC` | DECIMAL(18,2) | Part D per-capita |
| `ip_covered_days_per_1000_count` | `IP_Cvrd_Days_Per_1000` | DECIMAL(10,2) | Inpatient covered days per 1,000 benes |
| `ip_covered_stays_per_1000_count` | `IP_Cvrd_Stays_Per_1000` | DECIMAL(10,2) | Inpatient stays per 1,000 |
| `er_visits_per_1000_count` | `ER_Visits_Per_1000` | DECIMAL(10,2) | ER visit rate |
| `physician_events_per_1000_count` | `Phys_Events_Per_1000` | DECIMAL(10,2) | Physician encounter rate |
| `acute_hospital_readmission_rate` | `Acute_Hosp_Readmsn_Pct` | DECIMAL(7,4) | Readmission percentage |
| `data_year` | Derived from filename or metadata | SMALLINT | |
| `_loaded_at` | — | TIMESTAMP | dbt metadata |

> **Note**: CMS publishes additional chronic condition prevalence columns (`Benes_FFS_Pct_*` for diabetes, heart failure, COPD, etc.). These will be added as the schema evolves. The MVP staging model captures the most analytically critical fields first. A future `stg_cms__geographic_variation_conditions` model will handle the ~20 chronic condition prevalence columns.

### Intermediate: `int_geographic_benchmarks`

One row per geographic level + FIPS + data year. Derives additional benchmark metrics, normalizes geography, adds MA penetration rate.

| Column | Type | Source | Transform |
|--------|------|--------|-----------|
| `geographic_level` | VARCHAR(10) | `stg_cms__geographic_variation.geographic_level` | Direct |
| `state_fips` | VARCHAR(2) | `stg_cms__geographic_variation.state_fips` | Direct |
| `state_name` | VARCHAR(50) | `stg_cms__geographic_variation.state_name` | TRIM |
| `county_fips` | VARCHAR(5) | `stg_cms__geographic_variation.county_fips` | Direct; NULL for state/national rows |
| `county_name` | VARCHAR(100) | `stg_cms__geographic_variation.county_name` | TRIM |
| `data_year` | SMALLINT | Direct | |
| `ffs_beneficiary_count` | INTEGER | Direct | |
| `ma_beneficiary_count` | INTEGER | Direct | |
| `total_beneficiary_count` | INTEGER | Derived | `ffs_beneficiary_count + ma_beneficiary_count` |
| `dual_eligible_beneficiary_count` | INTEGER | Direct | |
| `ma_penetration_rate` | DECIMAL(7,4) | Derived | `ma_beneficiary_count / NULLIF(total_beneficiary_count, 0)` |
| `dual_eligible_rate` | DECIMAL(7,4) | Derived | `dual_eligible_beneficiary_count / NULLIF(total_beneficiary_count, 0)` |
| `beneficiary_age_lt65_count` | INTEGER | Direct | |
| `beneficiary_age_65_74_count` | INTEGER | Direct | |
| `beneficiary_age_75_84_count` | INTEGER | Direct | |
| `beneficiary_age_gt84_count` | INTEGER | Direct | |
| `pct_beneficiary_age_lt65` | DECIMAL(7,4) | Derived | Age distribution percentage |
| `pct_beneficiary_age_65_74` | DECIMAL(7,4) | Derived | |
| `pct_beneficiary_age_75_84` | DECIMAL(7,4) | Derived | |
| `pct_beneficiary_age_gt84` | DECIMAL(7,4) | Derived | |
| `avg_hcc_risk_score` | DECIMAL(7,4) | Direct | |
| `total_medicare_standardized_per_capita_amount` | DECIMAL(18,2) | Direct | |
| `total_medicare_actual_per_capita_amount` | DECIMAL(18,2) | Direct | |
| `ip_medicare_per_capita_amount` | DECIMAL(18,2) | Direct | |
| `pac_medicare_per_capita_amount` | DECIMAL(18,2) | Direct | |
| `physician_medicare_per_capita_amount` | DECIMAL(18,2) | Direct | |
| `op_medicare_per_capita_amount` | DECIMAL(18,2) | Direct | |
| `hh_medicare_per_capita_amount` | DECIMAL(18,2) | Direct | |
| `hospice_medicare_per_capita_amount` | DECIMAL(18,2) | Direct | |
| `dme_medicare_per_capita_amount` | DECIMAL(18,2) | Direct | |
| `partd_medicare_per_capita_amount` | DECIMAL(18,2) | Direct | |
| `ip_covered_days_per_1000_count` | DECIMAL(10,2) | Direct | |
| `ip_covered_stays_per_1000_count` | DECIMAL(10,2) | Direct | |
| `er_visits_per_1000_count` | DECIMAL(10,2) | Direct | |
| `physician_events_per_1000_count` | DECIMAL(10,2) | Direct | |
| `acute_hospital_readmission_rate` | DECIMAL(7,4) | Direct | |
| `physician_spending_as_pct_of_total` | DECIMAL(7,4) | Derived | `physician_per_capita / NULLIF(total_standardized_per_capita, 0)` |
| `ip_spending_as_pct_of_total` | DECIMAL(7,4) | Derived | Inpatient share of total |
| `partd_spending_as_pct_of_total` | DECIMAL(7,4) | Derived | Part D share of total |

### Mart: `ref_geographies`

Reference geography dimension. One row per geographic unit (state or county) from the most recent data year. Used as a join target.

| Column | Type | Aggregation | Notes |
|--------|------|------------|-------|
| `geographic_level` | VARCHAR(10) | -- | 'National', 'State', 'County' |
| `state_fips` | VARCHAR(2) | -- | Primary key component |
| `state_name` | VARCHAR(50) | -- | |
| `county_fips` | VARCHAR(5) | -- | Primary key (NULL for state/national) |
| `county_name` | VARCHAR(100) | -- | |
| `latest_ffs_beneficiary_count` | INTEGER | -- | From most recent year |
| `latest_ma_beneficiary_count` | INTEGER | -- | |
| `latest_total_beneficiary_count` | INTEGER | -- | |
| `latest_ma_penetration_rate` | DECIMAL(7,4) | -- | |
| `latest_avg_hcc_risk_score` | DECIMAL(7,4) | -- | |

### Mart: `mart_geographic__spending_variation`

One row per geography + data year. Includes all benchmarks plus year-over-year calculations.

| Column | Type | Aggregation | Notes |
|--------|------|------------|-------|
| `geographic_level` | VARCHAR(10) | -- | Group key |
| `state_fips` | VARCHAR(2) | -- | Group key |
| `state_name` | VARCHAR(50) | -- | |
| `county_fips` | VARCHAR(5) | -- | Group key (NULL for state/national) |
| `county_name` | VARCHAR(100) | -- | |
| `data_year` | SMALLINT | -- | Group key |
| `ffs_beneficiary_count` | INTEGER | -- | |
| `total_beneficiary_count` | INTEGER | -- | |
| `ma_penetration_rate` | DECIMAL(7,4) | -- | |
| `avg_hcc_risk_score` | DECIMAL(7,4) | -- | |
| `total_medicare_standardized_per_capita_amount` | DECIMAL(18,2) | -- | |
| `total_medicare_actual_per_capita_amount` | DECIMAL(18,2) | -- | |
| `ip_medicare_per_capita_amount` | DECIMAL(18,2) | -- | |
| `physician_medicare_per_capita_amount` | DECIMAL(18,2) | -- | |
| `partd_medicare_per_capita_amount` | DECIMAL(18,2) | -- | |
| `ip_covered_stays_per_1000_count` | DECIMAL(10,2) | -- | |
| `er_visits_per_1000_count` | DECIMAL(10,2) | -- | |
| `acute_hospital_readmission_rate` | DECIMAL(7,4) | -- | |
| `physician_spending_as_pct_of_total` | DECIMAL(7,4) | -- | |
| `ip_spending_as_pct_of_total` | DECIMAL(7,4) | -- | |
| `partd_spending_as_pct_of_total` | DECIMAL(7,4) | -- | |
| `yoy_standardized_per_capita_change_rate` | DECIMAL(7,4) | Window | `(current - prior) / prior` using LAG |
| `yoy_ip_stays_per_1000_change_rate` | DECIMAL(7,4) | Window | Year-over-year change |
| `yoy_er_visits_per_1000_change_rate` | DECIMAL(7,4) | Window | Year-over-year change |
| `national_standardized_per_capita_amount` | DECIMAL(18,2) | Window | National row value for same year (for index calculation) |
| `spending_index_vs_national` | DECIMAL(7,4) | Derived | `area_standardized_pc / national_standardized_pc` — values >1.0 = above national avg |

### Mart: `mart_geographic__by_state`

One row per state + data year. Cross-source mart combining Geographic Variation benchmarks with aggregated Part B and Part D provider-level data.

| Column | Type | Aggregation | Notes |
|--------|------|------------|-------|
| `state_fips` | VARCHAR(2) | -- | Group key |
| `state_name` | VARCHAR(50) | -- | |
| `data_year` | SMALLINT | -- | Group key |
| `ffs_beneficiary_count` | INTEGER | -- | From geo variation |
| `total_beneficiary_count` | INTEGER | -- | |
| `ma_penetration_rate` | DECIMAL(7,4) | -- | |
| `avg_hcc_risk_score` | DECIMAL(7,4) | -- | |
| `total_medicare_standardized_per_capita_amount` | DECIMAL(18,2) | -- | From geo variation |
| `partb_provider_count` | INTEGER | COUNT(DISTINCT NPI) | From Part B, aggregated to state |
| `partb_total_service_count` | BIGINT | SUM | From Part B, aggregated to state |
| `partb_total_payment_amount` | DECIMAL(18,2) | SUM | From Part B, aggregated to state |
| `partd_prescriber_count` | INTEGER | COUNT(DISTINCT NPI) | From Part D, aggregated to state |
| `partd_total_claim_count` | BIGINT | SUM | From Part D, aggregated to state |
| `partd_total_drug_cost_amount` | DECIMAL(18,2) | SUM | From Part D, aggregated to state |
| `partd_opioid_claim_count` | BIGINT | SUM | From Part D, opioid-flagged |
| `partd_opioid_claim_rate` | DECIMAL(7,4) | Ratio | Opioid claims / total claims |
| `spending_index_vs_national` | DECIMAL(7,4) | Derived | From geo variation |

## Keys & Indexes

| Model | Primary Key | Indexes | Foreign Keys |
|-------|------------|---------|--------------|
| `stg_cms__geographic_variation` | `geographic_level` + `state_fips` + `county_fips` + `data_year` | `state_fips`, `county_fips`, `data_year` | None |
| `int_geographic_benchmarks` | `geographic_level` + `state_fips` + `county_fips` + `data_year` | `state_fips`, `county_fips`, `data_year`, `geographic_level` | None |
| `ref_geographies` | `county_fips` (county), `state_fips` (state), `geographic_level` (national) | `state_fips`, `geographic_level` | None |
| `mart_geographic__spending_variation` | `geographic_level` + `state_fips` + `county_fips` + `data_year` | `state_fips`, `data_year`, `geographic_level` | `state_fips` -> `ref_geographies.state_fips` |
| `mart_geographic__by_state` | `state_fips` + `data_year` | `state_fips`, `data_year` | `state_fips` -> `ref_geographies.state_fips` |

## Evaluation

| Criterion | Verdict | Notes |
|-----------|---------|-------|
| Grain clearly defined | **PASS** | Staging/Int: geo_level + FIPS + year. Marts: geography + year at defined levels. |
| Naming conventions followed | **PASS** | `stg_cms__geographic_variation`, `int_geographic_benchmarks`, `mart_geographic__*`, `ref_geographies` |
| Types appropriate | **PASS** | FIPS as VARCHAR, per-capita amounts as DECIMAL(18,2), rates as DECIMAL(7,4), counts as INTEGER |
| No mixed concerns per model | **PASS** | Staging = source mirror; int = derived rates/shares; mart = cross-source aggregation + YOY |
| Relationships explicit | **PASS** | State FIPS links to provider data; geographic_level distinguishes rows |
| Codes stored as VARCHAR | **PASS** | State FIPS VARCHAR(2), County FIPS VARCHAR(5) |
| Money as DECIMAL | **PASS** | All per-capita amounts DECIMAL(18,2) |
| Healthcare domain patterns used | **PASS** | HCC risk scores, MA penetration, standardized vs. actual spending, service category breakdown, readmission rates |
| Scalable at projected volume | **PASS** | ~3,250 rows/year is tiny; indexes are for join efficiency, not scan performance |
| Lineage traceable raw->mart | **PASS** | CSV -> stg -> int_geographic_benchmarks -> mart_geographic__spending_variation / mart_geographic__by_state |

## Verdict: APPROVED

---

# Cross-Source Models

## Shared Dimensions

### `ref_providers` (from NPPES)

The master provider dimension. One row per NPI. All provider-level marts join to this table for provider identity enrichment.

- **Source**: `int_providers` (from NPPES)
- **Grain**: One row per NPI
- **Usage**: Joined by `mart_provider__practice_profile`, `mart_provider__prescribing_summary`, `mart_provider__by_specialty`, and any future provider-level mart
- **Key fields**: `npi`, `entity_type_name`, `provider_display_name`, `primary_taxonomy_code`, `practice_state_code`, `practice_zip5`, `is_active_flag`

### `ref_geographies` (from Geographic Variation + Census crosswalks)

The master geography dimension. One row per geographic unit (national, state, county).

- **Source**: `int_geographic_benchmarks` (from Geographic Variation), filtered to most recent data year
- **Grain**: One row per geographic_level + FIPS
- **Usage**: Joined by all geographic marts and for contextual enrichment of provider-level data
- **Key fields**: `state_fips`, `county_fips`, `state_name`, `county_name`, `latest_ffs_beneficiary_count`, `latest_ma_penetration_rate`
- **Future expansion**: Will be enriched with Census/ACS data (population, income, race/ethnicity) and HUD ZIP-to-county crosswalks

### `ref_hcpcs_codes` (reference table for procedure codes)

HCPCS code reference dimension. One row per HCPCS code.

- **Source**: Extracted from `stg_cms__part_b_utilization` (distinct HCPCS codes and descriptions), plus future enrichment from Medicare Fee Schedule PUF
- **Grain**: One row per HCPCS code
- **Usage**: Joined by `int_provider_services` and any service-level analysis

| Column | Type | Notes |
|--------|------|-------|
| `hcpcs_code` | VARCHAR(5) | Primary key |
| `hcpcs_description` | VARCHAR(500) | From Part B source |
| `is_drug_code_flag` | BOOLEAN | From `HCPCS_Drug_Ind` |
| `first_seen_year` | SMALLINT | Earliest year this code appears in data |
| `last_seen_year` | SMALLINT | Most recent year |

> **Note**: A comprehensive `ref_drugs` table is deferred to a future sprint. Drug name normalization (mapping variant brand/generic names to canonical identifiers) is a substantial effort. For MVP, Part D drug names are stored as-is in `int_provider_prescriptions`. The normalization strategy will be: build a mapping table from observed `drug_brand_name` + `drug_generic_name` pairs to canonical generic names, potentially linked to RxNorm CUIs or ATC codes.

## Cross-Source Marts

### `mart_provider__practice_profile` (Part B + Part D joined on NPI)

The flagship cross-source mart. One row per NPI + data year. Combines Part B service billing with Part D prescribing to create a comprehensive provider practice profile.

**Build strategy**: Start with `mart_provider__practice_profile` (Part B) and LEFT JOIN to `mart_provider__prescribing_summary` (Part D) on `rendering_npi = prescriber_npi` and `data_year`.

Additional columns from Part D join:

| Column | Type | Source |
|--------|------|--------|
| `partd_total_claim_count` | BIGINT | `mart_provider__prescribing_summary.total_claim_count` |
| `partd_total_drug_cost_amount` | DECIMAL(18,2) | `mart_provider__prescribing_summary.total_drug_cost_amount` |
| `partd_distinct_drug_count` | INTEGER | `mart_provider__prescribing_summary.distinct_drug_count` |
| `partd_opioid_claim_count` | BIGINT | `mart_provider__prescribing_summary.opioid_claim_count` |
| `partd_opioid_claim_rate` | DECIMAL(7,4) | `mart_provider__prescribing_summary.opioid_claim_rate` |
| `partd_antibiotic_claim_rate` | DECIMAL(7,4) | `mart_provider__prescribing_summary.antibiotic_claim_rate` |
| `total_medicare_spend_amount` | DECIMAL(18,2) | Part B payment + Part D drug cost |
| `has_partb_activity_flag` | BOOLEAN | Part B data exists for this NPI+year |
| `has_partd_activity_flag` | BOOLEAN | Part D data exists for this NPI+year |

**Why LEFT JOIN**: Not all Part B providers prescribe Part D drugs (e.g., surgeons), and not all Part D prescribers bill Part B (e.g., some NPs with prescribing-only roles). The LEFT JOIN from Part B preserves all Part B providers while adding Part D data where available.

### `mart_geographic__spending_variation` (Geo Variation + Part B + Part D aggregated by geography)

Defined above in the Geographic Variation section. This mart combines:

1. Geographic Variation population-level benchmarks (per-capita spending, utilization rates, HCC scores)
2. Aggregated Part B provider data by state (provider count, total services, total payments)
3. Aggregated Part D prescriber data by state (prescriber count, total claims, drug costs, opioid rates)

The state-level version is `mart_geographic__by_state`. The full version preserves county-level granularity for Geographic Variation columns (Part B/Part D data is aggregated to state, not county, because provider ZIP-to-county mapping is not yet implemented).

### `mart_geographic__by_state`

Defined above. This is the cross-source state-level summary combining all three data perspectives.

## SCD Strategy

### Type 1 (Overwrite) Entities

| Entity | Rationale |
|--------|-----------|
| `ref_hcpcs_codes.hcpcs_description` | Description text may be refined by CMS across years; we want the most current description. `first_seen_year` and `last_seen_year` track code lifecycle. |
| `ref_geographies.latest_*` columns | Always reflect the most recent year's population benchmarks. |

### Type 2 (Historical) Entities

| Entity | Rationale | Implementation |
|--------|-----------|----------------|
| `ref_providers` — address, taxonomy, credential | Providers change practice locations, add/remove specialties, and update credentials over time. For longitudinal analysis (e.g., "how many providers migrated from state X to state Y"), we need historical snapshots. | Monthly NPPES snapshots stored as `stg_cms__nppes_snapshot` with `snapshot_date` column. `ref_providers` is the **current** view (Type 1), while a future `dim_provider_history` model implements full Type 2 with `valid_from`, `valid_to`, `is_current_flag`. **Deferred to post-MVP** because: (a) NPPES does not provide historical files — we must build our own snapshot pipeline, and (b) the MVP data years span 2013-2022 but we only have the current NPPES file. Retroactive history is not possible without archived snapshots. |
| `ref_providers` — active/deactivated status | NPI deactivation and reactivation events. | Captured via `deactivation_date` and `reactivation_date` in the current model. Full event history is a Type 2 concern deferred to post-MVP. |

### Type 0 (Immutable) Entities

| Entity | Rationale |
|--------|-----------|
| `stg_cms__part_b_utilization` per year | Each annual file is a complete, immutable snapshot. We load it once and never update it. The `data_year` column partitions the data. |
| `stg_cms__part_d_prescribers` per year | Same — immutable annual snapshot. |
| `stg_cms__geographic_variation` per year | Same — immutable annual snapshot. |
| `ref_providers.npi` | An NPI, once assigned, is never reassigned to a different entity. The NPI itself is immutable even if the provider's attributes change. |

### MVP SCD Summary

For MVP, the practical strategy is:

1. **Provider dimension**: Type 1 (overwrite with latest NPPES data). No historical tracking until the snapshot pipeline is operational.
2. **Fact tables (Part B, Part D, Geo Variation)**: Type 0 (immutable per data year). Each year is loaded independently and never modified.
3. **Reference tables (HCPCS, geographies)**: Type 1 (overwrite with latest values).
4. **Post-MVP**: Implement Type 2 for the provider dimension once monthly NPPES snapshot capture is operational.

---

## dbt Project Structure (suggested)

```
models/
  staging/
    cms/
      _cms__sources.yml                       # dbt source definitions for raw CMS data
      _cms__models.yml                        # dbt model configs for staging layer
      stg_cms__nppes.sql                      # NPPES provider registry
      stg_cms__part_b_utilization.sql         # Part B physician/practitioner services
      stg_cms__part_d_prescribers.sql         # Part D prescriber-drug combinations
      stg_cms__geographic_variation.sql       # Geographic variation (national/state/county)
  intermediate/
    _int__models.yml                          # dbt model configs for intermediate layer
    int_providers.sql                         # Cleaned/enriched provider dimension
    int_provider_services.sql                 # Part B with derived totals
    int_provider_prescriptions.sql            # Part D with derived cost metrics
    int_geographic_benchmarks.sql             # Geo variation with derived rates
  marts/
    provider/
      _provider__models.yml                   # dbt model configs for provider marts
      mart_provider__practice_profile.sql     # Cross-source: Part B + Part D per NPI
      mart_provider__prescribing_summary.sql  # Part D prescribing aggregation per NPI
      mart_provider__by_specialty.sql         # Part B aggregation per specialty
    geographic/
      _geographic__models.yml                 # dbt model configs for geographic marts
      mart_geographic__spending_variation.sql # Full geographic benchmarks with YOY
      mart_geographic__by_state.sql           # Cross-source state-level summary
    reference/
      _reference__models.yml                  # dbt model configs for reference tables
      ref_providers.sql                       # Master provider dimension
      ref_provider_taxonomies.sql             # Unpivoted provider taxonomy codes
      ref_geographies.sql                     # Master geography dimension
      ref_hcpcs_codes.sql                     # HCPCS code reference
  _project.yml                                # dbt_project.yml configuration
```

### dbt Materialization Strategy

| Model | Materialization | Rationale |
|-------|----------------|-----------|
| `stg_cms__*` | `view` | Staging models are lightweight transforms; views avoid data duplication |
| `int_*` | `view` or `table` | Views for small sources (geo variation); tables for large sources (Part B, Part D) where derived columns benefit from pre-computation |
| `mart_*` | `table` | All marts are materialized tables for query performance |
| `ref_*` | `table` | Reference dimensions are materialized for join performance |

### dbt Testing Strategy

| Test Type | Applied To | Examples |
|-----------|-----------|---------|
| `unique` | All primary keys | `stg_cms__nppes.npi`, composite keys on all staging/int models |
| `not_null` | Primary keys, critical columns | NPI, HCPCS code, data_year, geographic_level |
| `accepted_values` | Enumerated fields | `entity_type_code` in ('1','2'), `place_of_service_code` in ('F','O'), `geographic_level` in ('National','State','County') |
| `relationships` | Foreign keys | `int_provider_services.rendering_npi` references `ref_providers.npi` |
| Custom: `positive_values` | Monetary and count columns | All `_amount`, `_count` fields >= 0 |
| Custom: `valid_npi` | NPI columns | 10-digit, passes Luhn check |
| Custom: `valid_fips` | FIPS columns | 2-digit state or 5-digit county |

---

## Overall Verdict: APPROVED

### Summary of Models

| Layer | Model | Grain | Estimated Rows |
|-------|-------|-------|----------------|
| Staging | `stg_cms__nppes` | 1 per NPI | ~8M |
| Staging | `stg_cms__part_b_utilization` | 1 per NPI+HCPCS+POS+year | ~10M/year |
| Staging | `stg_cms__part_d_prescribers` | 1 per NPI+drug+year | ~25M/year |
| Staging | `stg_cms__geographic_variation` | 1 per geo+FIPS+year | ~3.3K/year |
| Intermediate | `int_providers` | 1 per NPI | ~8M |
| Intermediate | `int_provider_services` | 1 per NPI+HCPCS+POS+year | ~10M/year |
| Intermediate | `int_provider_prescriptions` | 1 per NPI+drug+year | ~25M/year |
| Intermediate | `int_geographic_benchmarks` | 1 per geo+FIPS+year | ~3.3K/year |
| Mart | `ref_providers` | 1 per NPI | ~8M |
| Mart | `ref_provider_taxonomies` | 1 per NPI+taxonomy | ~10M (avg 1.3 taxonomies/NPI) |
| Mart | `ref_geographies` | 1 per geographic unit | ~3.3K |
| Mart | `ref_hcpcs_codes` | 1 per HCPCS code | ~10K |
| Mart | `mart_provider__practice_profile` | 1 per NPI+year | ~1.2M/year |
| Mart | `mart_provider__prescribing_summary` | 1 per NPI+year | ~1.1M/year |
| Mart | `mart_provider__by_specialty` | 1 per specialty+year | ~100-200 |
| Mart | `mart_geographic__spending_variation` | 1 per geo+FIPS+year | ~3.3K/year |
| Mart | `mart_geographic__by_state` | 1 per state+year | ~55/year |

### Design Decisions Log

| Decision | Rationale |
|----------|-----------|
| NPI as VARCHAR(10), not INTEGER | Leading zeros possible in theory; consistency with all CMS documentation; prevents accidental arithmetic |
| FIPS as VARCHAR(2) / VARCHAR(5) | Leading zeros are significant (e.g., state FIPS '01' for Alabama, county FIPS '01001') |
| HCPCS as VARCHAR(5) | Mix of numeric CPT codes and alphanumeric Level II codes (e.g., 'J1234') |
| All money as DECIMAL(18,2) | IEEE 754 floating-point would introduce rounding errors in financial aggregation |
| `data_year` as SMALLINT, not DATE | Source data is annual; no day-level precision needed; simplifies partitioning and joins |
| Taxonomy unpivoted into separate model | 15 wide columns in NPPES are denormalized; unpivoting enables specialty-based queries without 15 OR conditions |
| Part B totals derived in intermediate layer | Source provides averages only; `total = avg * count` is calculated once in int layer, not repeatedly in marts |
| Part D drug names left as-is for MVP | Drug name normalization is a substantial project; deferred to dedicated sprint with RxNorm/NDC mapping |
| SCD Type 2 deferred for providers | Requires monthly snapshot pipeline not yet built; NPPES has no historical file; MVP uses Type 1 (current state) |
| LEFT JOIN for Part B + Part D cross-source mart | Not all Part B providers prescribe, not all prescribers bill Part B; preserves both populations |
| Chronic condition prevalence columns deferred | ~20 additional columns in geo variation; modeled as future expansion to keep MVP scope manageable |
| RUCA code stored as VARCHAR(10) | RUCA codes include decimal subcategories (e.g., '1.0', '1.1'); VARCHAR preserves precision |

### Risks and Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| Column naming drift across CMS data years | MEDIUM | Schema registry in `_cms__sources.yml`; version-specific column mappings in staging SQL |
| Part D drug name inconsistency | MEDIUM | MVP defers normalization; future `ref_drugs` with mapping table |
| ZIP-to-county crosswalk imprecision | LOW | Deferred to post-MVP; state-level joins used for now |
| NPPES file size (~10 GB uncompressed) | LOW | DuckDB handles this efficiently; PostgreSQL with COPY command; no row-level API needed |
| CMS suppression creating systematic gaps | LOW | Document in all marts; never claim totals match CMS national statistics |
| MA penetration making FFS data less representative over time | MEDIUM | MA penetration rate included in all geographic marts as a mandatory contextual variable |

### Next Steps

1. **Pipeline Architect** designs the 7-stage lifecycle for each of the 4 sources based on these models
2. **Implement dbt project skeleton** with source definitions and staging models
3. **Acquire first data year** (recommend most recent available, likely 2022) for each source
4. **Build and test staging models** before proceeding to intermediate and mart layers
5. **Drug name normalization sprint** (separate task) to build `ref_drugs`
6. **NPPES snapshot pipeline** (separate task) to enable Type 2 SCD for providers
