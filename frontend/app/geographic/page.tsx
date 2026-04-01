/**
 * Geographic Explorer — state-level spending variation and benchmarks.
 */

"use client";

import { useEffect, useState } from "react";
import { getSpendingVariation, type StateSpending } from "@/lib/api";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/format";
import DataTable from "@/components/data-table";
import KpiCard from "@/components/kpi-card";

export default function GeographicPage() {
  const [dataYear, setDataYear] = useState("2022");
  const [states, setStates] = useState<StateSpending[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    getSpendingVariation(dataYear)
      .then(setStates)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [dataYear]);

  const avgSpending = states.length > 0
    ? states.reduce((sum, s) => sum + (s.actual_per_capita_costs || 0), 0) / states.length
    : 0;
  const highSpending = states.filter((s) => (s.spending_index || 0) > 1.1).length;
  const lowSpending = states.filter((s) => (s.spending_index || 0) < 0.9).length;

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">Geographic Explorer</h1>
        <select
          value={dataYear}
          onChange={(e) => setDataYear(e.target.value)}
          className="rounded border border-slate-300 px-3 py-2 text-sm"
        >
          {[2022, 2021, 2020].map((y) => (
            <option key={y} value={y}>{y}</option>
          ))}
        </select>
      </div>

      {loading && <div className="text-slate-500">Loading geographic data...</div>}
      {error && <div className="text-red-600">Error: {error}</div>}

      {!loading && !error && (
        <>
          <div className="mb-8 grid grid-cols-1 gap-6 md:grid-cols-3">
            <KpiCard label="States Tracked" value={formatNumber(states.length)} />
            <KpiCard label="Above Average Spending" value={`${highSpending} states`} />
            <KpiCard label="Below Average Spending" value={`${lowSpending} states`} />
          </div>

          <div className="rounded-lg border border-slate-200 bg-white">
            <DataTable
              columns={[
                { key: "state_abbreviation", label: "State" },
                { key: "state_name", label: "Name" },
                { key: "actual_per_capita_costs", label: "Per Capita $", align: "right", format: (v) => formatCurrency(v as number) },
                { key: "spending_index", label: "Spending Index", align: "right", format: (v) => (v as number)?.toFixed(3) || "N/A" },
                { key: "ma_participation_rate", label: "MA Rate", align: "right", format: (v) => formatPercent(v ? (v as number) * 100 : null) },
                { key: "provider_count", label: "Providers", align: "right", format: (v) => formatNumber(v as number) },
                { key: "providers_per_1000_benes", label: "Per 1K Benes", align: "right", format: (v) => (v as number)?.toFixed(1) || "N/A" },
              ]}
              data={states}
            />
          </div>
        </>
      )}
    </div>
  );
}
