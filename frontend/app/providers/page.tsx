/**
 * Provider Lookup — search and view provider profiles.
 */

"use client";

import { useState } from "react";
import { searchProviders, getProvider, type ProviderProfile, type ProviderSummary } from "@/lib/api";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/format";
import DataTable from "@/components/data-table";

export default function ProvidersPage() {
  const [query, setQuery] = useState("");
  const [stateFilter, setState] = useState("");
  const [results, setResults] = useState<ProviderSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [selected, setSelected] = useState<ProviderProfile | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async () => {
    setLoading(true);
    setError(null);
    setSelected(null);
    try {
      const params: Record<string, string> = {};
      // Check if query is an NPI (10 digits)
      if (/^\d{10}$/.test(query)) {
        const provider = await getProvider(query);
        setSelected(provider);
        setResults([]);
        setTotal(0);
        return;
      }
      if (query) params.name = query;
      if (stateFilter) params.state = stateFilter;
      params.page_size = "50";
      const res = await searchProviders(params);
      setResults(res.items);
      setTotal(res.total);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Search failed");
    } finally {
      setLoading(false);
    }
  };

  const handleRowClick = async (row: ProviderSummary) => {
    try {
      const provider = await getProvider(row.npi);
      setSelected(provider);
    } catch {
      setError("Failed to load provider details");
    }
  };

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-slate-900">Provider Lookup</h1>

      <div className="mb-6 flex gap-4">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          placeholder="Search by NPI or provider name..."
          className="flex-1 rounded-lg border border-slate-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none"
        />
        <input
          type="text"
          value={stateFilter}
          onChange={(e) => setState(e.target.value.toUpperCase())}
          placeholder="State"
          maxLength={2}
          className="w-20 rounded-lg border border-slate-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none"
        />
        <button
          onClick={handleSearch}
          disabled={loading}
          className="rounded-lg bg-blue-600 px-6 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? "Searching..." : "Search"}
        </button>
      </div>

      {error && <div className="mb-4 text-sm text-red-600">{error}</div>}

      {selected && (
        <div className="mb-8 rounded-lg border border-slate-200 bg-white p-6">
          <div className="mb-4 flex items-start justify-between">
            <div>
              <h2 className="text-xl font-bold text-slate-900">{selected.display_name}</h2>
              <p className="text-sm text-slate-500">NPI: {selected.npi} | {selected.entity_type}</p>
            </div>
            <button onClick={() => setSelected(null)} className="text-sm text-slate-400 hover:text-slate-600">Close</button>
          </div>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
            <div>
              <h3 className="mb-2 text-sm font-semibold text-slate-600">Location</h3>
              <p className="text-sm">{selected.practice_city}, {selected.practice_state}</p>
              <p className="text-sm text-slate-500">{String(selected.state_name || "")}</p>
            </div>
            <div>
              <h3 className="mb-2 text-sm font-semibold text-slate-600">Specialty</h3>
              <p className="text-sm">{String(selected.specialty_classification || "N/A")}</p>
              <p className="text-sm text-slate-500">{String(selected.specialty_display_name || "")}</p>
            </div>
            <div>
              <h3 className="mb-2 text-sm font-semibold text-slate-600">Medicare Activity</h3>
              {selected.has_part_b_data && (
                <>
                  <p className="text-sm">Services: {formatNumber(selected.total_services_rendered)}</p>
                  <p className="text-sm">Payments: {formatCurrency(selected.total_medicare_payments)}</p>
                </>
              )}
              {selected.has_part_d_data && (
                <>
                  <p className="text-sm">Rx Claims: {formatNumber(selected.total_drugs_prescribed)}</p>
                  <p className="text-sm">
                    Opioid: {selected.has_opioid_prescriptions ? "Yes" : "No"}
                  </p>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {results.length > 0 && (
        <div>
          <p className="mb-3 text-sm text-slate-500">{formatNumber(total)} providers found</p>
          <div className="rounded-lg border border-slate-200 bg-white">
            <DataTable
              columns={[
                { key: "npi", label: "NPI" },
                { key: "display_name", label: "Name" },
                { key: "entity_type", label: "Type" },
                { key: "practice_state", label: "State" },
                { key: "practice_city", label: "City" },
                { key: "specialty_classification", label: "Specialty" },
                { key: "total_medicare_payments", label: "Medicare $", align: "right", format: (v) => formatCurrency(v as number) },
              ]}
              data={results}
              onRowClick={handleRowClick}
            />
          </div>
        </div>
      )}
    </div>
  );
}
