/**
 * Specialty Comparison — compare provider specialties by volume and spending.
 */

"use client";

import { useEffect, useState } from "react";
import { getSpecialties, getSpecialtyDetail, type SpecialtySummary, type SpecialtyDetail } from "@/lib/api";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/format";
import DataTable from "@/components/data-table";

export default function SpecialtiesPage() {
  const [specialties, setSpecialties] = useState<SpecialtySummary[]>([]);
  const [selected, setSelected] = useState<SpecialtyDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getSpecialties()
      .then(setSpecialties)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const handleRowClick = async (row: SpecialtySummary) => {
    try {
      const detail = await getSpecialtyDetail(row.specialty_classification);
      setSelected(detail);
    } catch {
      setError("Failed to load specialty details");
    }
  };

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-slate-900">Specialty Comparison</h1>

      {loading && <div className="text-slate-500">Loading specialties...</div>}
      {error && <div className="mb-4 text-red-600">Error: {error}</div>}

      {selected && (
        <div className="mb-8 rounded-lg border border-blue-200 bg-blue-50 p-6">
          <div className="flex items-start justify-between">
            <h2 className="text-lg font-bold text-slate-900">{selected.specialty_classification}</h2>
            <button onClick={() => setSelected(null)} className="text-sm text-slate-400 hover:text-slate-600">Close</button>
          </div>
          <div className="mt-4 grid grid-cols-2 gap-4 md:grid-cols-4">
            <div>
              <p className="text-xs text-slate-500">Providers</p>
              <p className="text-lg font-semibold">{formatNumber(selected.provider_count)}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Total Medicare Payments</p>
              <p className="text-lg font-semibold">{formatCurrency(selected.total_medicare_payments)}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Avg Payment/Provider</p>
              <p className="text-lg font-semibold">{formatCurrency(selected.avg_payment_per_provider)}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Total Drug Cost</p>
              <p className="text-lg font-semibold">{formatCurrency(selected.total_drug_cost)}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Generic Rate</p>
              <p className="text-lg font-semibold">{formatPercent(selected.avg_generic_rate)}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Opioid Prescribers</p>
              <p className="text-lg font-semibold">{formatNumber(selected.opioid_prescriber_count)}</p>
            </div>
          </div>
        </div>
      )}

      {!loading && specialties.length > 0 && (
        <div className="rounded-lg border border-slate-200 bg-white">
          <DataTable
            columns={[
              { key: "specialty_classification", label: "Specialty" },
              { key: "provider_count", label: "Providers", align: "right", format: (v) => formatNumber(v as number) },
              { key: "total_medicare_payments", label: "Total Payments", align: "right", format: (v) => formatCurrency(v as number) },
              { key: "avg_payment_per_provider", label: "Avg/Provider", align: "right", format: (v) => formatCurrency(v as number) },
            ]}
            data={specialties}
            onRowClick={handleRowClick}
          />
        </div>
      )}
    </div>
  );
}
