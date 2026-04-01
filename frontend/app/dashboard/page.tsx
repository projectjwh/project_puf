/**
 * National Dashboard — high-level KPIs and trends.
 */

"use client";

import { useEffect, useState } from "react";
import KpiCard from "@/components/kpi-card";
import { getNationalKPIs, type NationalKPI } from "@/lib/api";
import { formatCompact, formatNumber, formatPercent } from "@/lib/format";

export default function DashboardPage() {
  const [kpis, setKpis] = useState<NationalKPI[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getNationalKPIs()
      .then(setKpis)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-slate-500">Loading national KPIs...</div>;
  if (error) return <div className="text-red-600">Error: {error}</div>;

  const latest = kpis[0];
  if (!latest) return <div className="text-slate-500">No KPI data available</div>;

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-slate-900">National Dashboard</h1>
      <p className="mb-8 text-sm text-slate-500">Data Year: {latest.data_year}</p>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          label="Total Medicare Payments"
          value={formatCompact(latest.national_total_medicare_payments)}
          change={latest.yoy_payment_change_pct}
        />
        <KpiCard
          label="Active Providers (Part B)"
          value={formatNumber(latest.active_providers_partb)}
        />
        <KpiCard
          label="Total Drug Spending"
          value={formatCompact(latest.national_total_drug_cost)}
          change={latest.yoy_drug_cost_change_pct}
        />
        <KpiCard
          label="Per Capita Costs"
          value={formatCompact(latest.national_per_capita_costs)}
        />
      </div>

      <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          label="Active Prescribers"
          value={formatNumber(latest.active_prescribers)}
        />
        <KpiCard
          label="MA Participation Rate"
          value={formatPercent(latest.national_ma_rate ? latest.national_ma_rate * 100 : null)}
        />
        <KpiCard
          label="Opioid Prescribers"
          value={formatNumber(latest.opioid_prescribers)}
        />
        <KpiCard
          label="High Opioid Prescribers"
          value={formatNumber(latest.high_opioid_prescribers)}
        />
      </div>

      {kpis.length > 1 && (
        <div className="mt-10">
          <h2 className="mb-4 text-lg font-semibold text-slate-800">Year-over-Year Trends</h2>
          <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase text-slate-500">Year</th>
                  <th className="px-4 py-3 text-right text-xs font-medium uppercase text-slate-500">Medicare Payments</th>
                  <th className="px-4 py-3 text-right text-xs font-medium uppercase text-slate-500">Drug Cost</th>
                  <th className="px-4 py-3 text-right text-xs font-medium uppercase text-slate-500">Providers</th>
                  <th className="px-4 py-3 text-right text-xs font-medium uppercase text-slate-500">Per Capita</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {kpis.map((kpi) => (
                  <tr key={kpi.data_year}>
                    <td className="px-4 py-3 text-sm font-medium text-slate-900">{kpi.data_year}</td>
                    <td className="px-4 py-3 text-right text-sm text-slate-700">{formatCompact(kpi.national_total_medicare_payments)}</td>
                    <td className="px-4 py-3 text-right text-sm text-slate-700">{formatCompact(kpi.national_total_drug_cost)}</td>
                    <td className="px-4 py-3 text-right text-sm text-slate-700">{formatNumber(kpi.active_providers_partb)}</td>
                    <td className="px-4 py-3 text-right text-sm text-slate-700">{formatCompact(kpi.national_per_capita_costs)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
