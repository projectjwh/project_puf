/**
 * API client for Project PUF backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function fetchAPI<T>(path: string, params?: Record<string, string>): Promise<T> {
  const url = new URL(`${API_BASE}${path}`);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        url.searchParams.set(key, value);
      }
    });
  }

  const res = await fetch(url.toString(), { next: { revalidate: 300 } });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

// Provider endpoints
export const getProvider = (npi: string) =>
  fetchAPI<ProviderProfile>(`/providers/${npi}`);

export const searchProviders = (params: Record<string, string>) =>
  fetchAPI<ProviderSearchResponse>("/providers", params);

// Geographic endpoints
export const getSpendingVariation = (dataYear: string) =>
  fetchAPI<StateSpending[]>("/geographic/spending", { data_year: dataYear });

export const getStates = (dataYear: string) =>
  fetchAPI<StateSummary[]>("/geographic/states", { data_year: dataYear });

// National endpoints
export const getNationalKPIs = () =>
  fetchAPI<NationalKPI[]>("/national/kpis");

// Opioid endpoints
export const getOpioidByState = (dataYear: string) =>
  fetchAPI<OpioidByState[]>("/opioid/by-state", { data_year: dataYear });

export const getTopOpioidPrescribers = (dataYear: string, state?: string) =>
  fetchAPI<OpioidTopPrescriber[]>("/opioid/top-prescribers", {
    data_year: dataYear,
    ...(state ? { state } : {}),
  });

// Specialty endpoints
export const getSpecialties = () =>
  fetchAPI<SpecialtySummary[]>("/specialties");

export const getSpecialtyDetail = (specialty: string) =>
  fetchAPI<SpecialtyDetail>(`/specialties/${encodeURIComponent(specialty)}`);

// Types (mirror API schemas)
export interface ProviderProfile {
  npi: string;
  display_name: string;
  entity_type?: string;
  practice_state?: string;
  practice_city?: string;
  specialty_classification?: string;
  specialty_display_name?: string;
  total_services_rendered?: number;
  total_medicare_payments?: number;
  total_drugs_prescribed?: number;
  has_opioid_prescriptions?: boolean;
  has_part_b_data?: boolean;
  has_part_d_data?: boolean;
  [key: string]: unknown;
}

export interface ProviderSearchResponse {
  items: ProviderSummary[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

export interface ProviderSummary {
  npi: string;
  display_name: string;
  entity_type?: string;
  practice_state?: string;
  practice_city?: string;
  specialty_classification?: string;
  total_medicare_payments?: number;
}

export interface NationalKPI {
  data_year: number;
  active_providers_partb?: number;
  active_prescribers?: number;
  national_total_medicare_payments?: number;
  national_total_drug_cost?: number;
  national_per_capita_costs?: number;
  national_ma_rate?: number;
  yoy_payment_change_pct?: number;
  yoy_drug_cost_change_pct?: number;
  [key: string]: unknown;
}

export interface StateSpending {
  state_fips: string;
  state_name?: string;
  state_abbreviation?: string;
  data_year: number;
  spending_index?: number;
  actual_per_capita_costs?: number;
  ma_participation_rate?: number;
  provider_count?: number;
  [key: string]: unknown;
}

export interface StateSummary {
  state_fips: string;
  state_name?: string;
  state_abbreviation?: string;
  data_year: number;
  total_beneficiaries?: number;
  total_providers?: number;
  spending_index?: number;
}

export interface OpioidByState {
  state_fips: string;
  state_name?: string;
  state_abbreviation?: string;
  data_year: number;
  opioid_prescriber_rate_pct?: number;
  opioid_claim_share_pct?: number;
  total_opioid_claims?: number;
  [key: string]: unknown;
}

export interface OpioidTopPrescriber {
  prescriber_npi: string;
  display_name?: string;
  practice_state?: string;
  opioid_claims?: number;
  opioid_claim_rate_pct?: number;
  state_opioid_rank?: number;
  [key: string]: unknown;
}

export interface SpecialtySummary {
  specialty_classification: string;
  provider_count: number;
  total_medicare_payments?: number;
  avg_payment_per_provider?: number;
}

export interface SpecialtyDetail extends SpecialtySummary {
  total_drug_cost?: number;
  avg_generic_rate?: number;
  opioid_prescriber_count?: number;
}
