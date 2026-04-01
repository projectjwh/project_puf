/**
 * Opioid Monitor — state-level opioid prescribing metrics and top prescribers.
 */

"use client";

import { useEffect, useState } from "react";
import { getOpioidByState, getTopOpioidPrescribers, type OpioidByState, type OpioidTopPrescriber } from "@/lib/api";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/format";
import DataTable from "@/components/data-table";
import KpiCard from "@/components/kpi-card";

export default function OpioidPage() {
  const [dataYear, setDataYear] = useState("2022");
  const [stateData, setStateData] = useState<OpioidByState[]>([]);
  const [topPrescribers, setTopPrescribers] = useState<OpioidTopPrescriber[]>([]);
  const [selectedState, setSelectedState] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      getOpioidByState(dataYear),
      getTopOpioidPrescribers(dataYear, selectedState || undefined),
    ])
      .then(([states, prescribers]) => {
        setStateData(states);
        setTopPrescribers(prescribers);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [dataYear, selectedState]);

  const totalOpioidClaims = stateData.reduce((sum, s) => sum + (s.total_opioid_claims || 0), 0);
  const avgRate = stateData.length > 0
    ? stateData.reduce((sum, s) => sum + (s.opioid_claim_share_pct || 0), 0) / stateData.length
    : 0;

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">Opioid Monitor</h1>
        <div className="flex gap-4">
          <select
            value={selectedState}
            onChange={(e) => setSelectedState(e.target.value)}
            className="rounded border border-slate-300 px-3 py-2 text-sm"
          >
            <option value="">All States</option>
            {stateData.map((s) => (
              <option key={s.state_fips} value={s.state_abbreviation || ""}>
                {s.state_name || s.state_abbreviation}
              </option>
            ))}
          </select>
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
      </div>

      {loading && <div className="text-slate-500">Loading opioid data...</div>}
      {error && <div className="text-red-600">Error: {error}</div>}

      {!loading && !error && (
        <>
          <div className="mb-8 grid grid-cols-1 gap-6 md:grid-cols-3">
            <KpiCard label="Total Opioid Claims" value={formatNumber(totalOpioidClaims)} />
            <KpiCard label="Avg Opioid Claim Share" value={formatPercent(avgRate)} />
            <KpiCard label="States Tracked" value={formatNumber(stateData.length)} />
          </div>

          <h2 className="mb-4 text-lg font-semibold text-slate-800">By State</h2>
          <div className="mb-8 rounded-lg border border-slate-200 bg-white">
            <DataTable
              columns={[
                { key: "state_abbreviation", label: "State" },
                { key: "state_name", label: "Name" },
                { key: "opioid_prescriber_rate_pct", label: "Prescriber Rate", align: "right", format: (v) => formatPercent(v as number) },
                { key: "opioid_claim_share_pct", label: "Claim Share", align: "right", format: (v) => formatPercent(v as number) },
                { key: "total_opioid_claims", label: "Opioid Claims", align: "right", format: (v) => formatNumber(v as number) },
                { key: "high_opioid_prescribers", label: "High Prescribers", align: "right", format: (v) => formatNumber(v as number) },
              ]}
              data={stateData}
            />
          </div>

          <h2 className="mb-4 text-lg font-semibold text-slate-800">Top Opioid Prescribers</h2>
          <div className="rounded-lg border border-slate-200 bg-white">
            <DataTable
              columns={[
                { key: "state_opioid_rank", label: "#", align: "right" },
                { key: "display_name", label: "Provider" },
                { key: "practice_state", label: "State" },
                { key: "opioid_claims", label: "Opioid Claims", align: "right", format: (v) => formatNumber(v as number) },
                { key: "opioid_claim_rate_pct", label: "Opioid %", align: "right", format: (v) => formatPercent(v as number) },
                { key: "opioid_drug_cost" as keyof OpioidTopPrescriber, label: "Opioid Cost", align: "right", format: (v) => formatCurrency(v as number) },
              ]}
              data={topPrescribers}
            />
          </div>
        </>
      )}
    </div>
  );
}
