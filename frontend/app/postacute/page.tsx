"use client";

import { useEffect, useState } from "react";
import DataTable from "@/components/data-table";
import FilterBar from "@/components/filter-bar";
import KpiCard from "@/components/kpi-card";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/format";

interface SNFData {
  ccn: string;
  facility_name: string;
  provider_state: string;
  overall_rating: number | null;
  staffing_rating: number | null;
  rn_staffing_rating: number | null;
  total_number_of_penalties: number | null;
  total_fine_amount: number | null;
  actual_rn_ratio: number | null;
  staffing_consistency_flag: string | null;
}

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export default function PostAcutePage() {
  const [snfData, setSnfData] = useState<SNFData[]>([]);
  const [state, setState] = useState("");
  const [minRating, setMinRating] = useState("");
  const [tab, setTab] = useState<"snf" | "hha" | "hospice">("snf");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (tab !== "snf") return;
    setLoading(true);
    const params = new URLSearchParams({ limit: "200" });
    if (state) params.set("state", state);
    if (minRating) params.set("min_rating", minRating);

    fetch(`${API}/postacute/snf?${params}`)
      .then((r) => r.json())
      .then(setSnfData)
      .catch(() => setSnfData([]))
      .finally(() => setLoading(false));
  }, [state, minRating, tab]);

  const avgRating = snfData.length
    ? snfData.reduce((s, d) => s + (d.overall_rating || 0), 0) / snfData.length
    : 0;
  const totalPenalties = snfData.reduce(
    (s, d) => s + (d.total_number_of_penalties || 0),
    0
  );

  const snfColumns = [
    { key: "ccn", label: "CCN" },
    { key: "facility_name", label: "Facility" },
    { key: "provider_state", label: "State" },
    {
      key: "overall_rating",
      label: "Overall",
      render: (v: number | null) => (v != null ? `${"★".repeat(v)}${"☆".repeat(5 - v)}` : "N/A"),
    },
    {
      key: "staffing_rating",
      label: "Staffing",
      render: (v: number | null) => (v != null ? `${v}/5` : "N/A"),
    },
    {
      key: "actual_rn_ratio",
      label: "RN Ratio",
      render: (v: number | null) => (v != null ? formatPercent(v * 100) : "N/A"),
    },
    {
      key: "total_number_of_penalties",
      label: "Penalties",
      render: (v: number | null) => formatNumber(v || 0),
    },
    {
      key: "total_fine_amount",
      label: "Fines",
      render: (v: number | null) => formatCurrency(v || 0),
    },
    {
      key: "staffing_consistency_flag",
      label: "Staffing Check",
    },
  ];

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-slate-900">Post-Acute Care</h2>

      <div className="flex gap-2">
        {(["snf", "hha", "hospice"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`rounded-md px-4 py-2 text-sm font-medium ${
              tab === t
                ? "bg-blue-600 text-white"
                : "bg-slate-100 text-slate-700"
            }`}
          >
            {t === "snf" ? "Skilled Nursing" : t === "hha" ? "Home Health" : "Hospice"}
          </button>
        ))}
      </div>

      {tab === "snf" && (
        <>
          <FilterBar
            filters={[
              {
                type: "search",
                label: "State",
                value: state,
                onChange: setState,
                placeholder: "e.g. CA",
              },
              {
                type: "select",
                label: "Min Rating",
                value: minRating,
                onChange: setMinRating,
                options: [
                  { value: "", label: "All" },
                  { value: "3", label: "3+ Stars" },
                  { value: "4", label: "4+ Stars" },
                  { value: "5", label: "5 Stars" },
                ],
              },
            ]}
          />
          <div className="grid grid-cols-3 gap-4">
            <KpiCard label="Facilities" value={formatNumber(snfData.length)} />
            <KpiCard label="Avg Rating" value={avgRating.toFixed(1)} />
            <KpiCard label="Total Penalties" value={formatNumber(totalPenalties)} />
          </div>
          {loading ? (
            <p className="text-slate-500">Loading...</p>
          ) : (
            <DataTable columns={snfColumns} data={snfData} pageSize={25} />
          )}
        </>
      )}

      {tab === "hha" && (
        <p className="text-slate-500">
          Home Health Agency data — select a state to view HHA quality metrics.
        </p>
      )}

      {tab === "hospice" && (
        <p className="text-slate-500">
          Hospice data — select a state to view hospice quality metrics.
        </p>
      )}
    </div>
  );
}
