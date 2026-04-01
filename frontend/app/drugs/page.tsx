"use client";

import { useEffect, useState } from "react";
import DataTable from "@/components/data-table";
import FilterBar from "@/components/filter-bar";
import KpiCard from "@/components/kpi-card";
import { formatCurrency, formatNumber } from "@/lib/format";

interface MedicaidDrugUtil {
  state: string;
  state_name: string;
  data_year: number;
  unique_drugs: number | null;
  total_prescriptions: number | null;
  total_reimbursed: number | null;
  avg_cost_per_prescription: number | null;
  medicaid_share_pct: number | null;
}

interface DrugPrice {
  hcpcs_code: string;
  short_description: string;
  payment_limit: number | null;
  dosage_form: string;
  quarter: number;
  year: number;
}

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export default function DrugSpendingPage() {
  const [utilData, setUtilData] = useState<MedicaidDrugUtil[]>([]);
  const [priceData, setPriceData] = useState<DrugPrice[]>([]);
  const [year, setYear] = useState(2022);
  const [hcpcsSearch, setHcpcsSearch] = useState("");
  const [tab, setTab] = useState<"utilization" | "pricing">("utilization");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(`${API}/drugs/medicaid-utilization?data_year=${year}`)
      .then((r) => r.json())
      .then(setUtilData)
      .catch(() => setUtilData([]))
      .finally(() => setLoading(false));
  }, [year]);

  useEffect(() => {
    if (hcpcsSearch.length >= 4) {
      fetch(`${API}/drugs/price-trends/${hcpcsSearch}`)
        .then((r) => r.json())
        .then(setPriceData)
        .catch(() => setPriceData([]));
    }
  }, [hcpcsSearch]);

  const totalReimbursed = utilData.reduce((s, d) => s + (d.total_reimbursed || 0), 0);
  const totalRx = utilData.reduce((s, d) => s + (d.total_prescriptions || 0), 0);

  const utilColumns = [
    { key: "state", label: "State" },
    { key: "state_name", label: "State Name" },
    {
      key: "total_prescriptions",
      label: "Prescriptions",
      render: (v: number | null) => formatNumber(v || 0),
    },
    {
      key: "total_reimbursed",
      label: "Total Reimbursed",
      render: (v: number | null) => formatCurrency(v || 0),
    },
    {
      key: "avg_cost_per_prescription",
      label: "Avg Cost/Rx",
      render: (v: number | null) => formatCurrency(v || 0),
    },
    {
      key: "unique_drugs",
      label: "Unique Drugs",
      render: (v: number | null) => formatNumber(v || 0),
    },
  ];

  const priceColumns = [
    { key: "hcpcs_code", label: "HCPCS" },
    { key: "short_description", label: "Description" },
    { key: "year", label: "Year" },
    { key: "quarter", label: "Quarter" },
    {
      key: "payment_limit",
      label: "Payment Limit",
      render: (v: number | null) => (v != null ? `$${v.toFixed(4)}` : "N/A"),
    },
    { key: "dosage_form", label: "Dosage Form" },
  ];

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-slate-900">Drug Spending Explorer</h2>

      <div className="flex gap-2">
        <button
          onClick={() => setTab("utilization")}
          className={`rounded-md px-4 py-2 text-sm font-medium ${
            tab === "utilization"
              ? "bg-blue-600 text-white"
              : "bg-slate-100 text-slate-700"
          }`}
        >
          Medicaid Utilization
        </button>
        <button
          onClick={() => setTab("pricing")}
          className={`rounded-md px-4 py-2 text-sm font-medium ${
            tab === "pricing"
              ? "bg-blue-600 text-white"
              : "bg-slate-100 text-slate-700"
          }`}
        >
          ASP Price Trends
        </button>
      </div>

      {tab === "utilization" && (
        <>
          <FilterBar
            filters={[
              {
                type: "select",
                label: "Year",
                value: String(year),
                onChange: (v) => setYear(Number(v)),
                options: [
                  { value: "2020", label: "2020" },
                  { value: "2021", label: "2021" },
                  { value: "2022", label: "2022" },
                ],
              },
            ]}
          />
          <div className="grid grid-cols-2 gap-4">
            <KpiCard label="Total Medicaid Reimbursed" value={formatCurrency(totalReimbursed)} />
            <KpiCard label="Total Prescriptions" value={formatNumber(totalRx)} />
          </div>
          {loading ? (
            <p className="text-slate-500">Loading...</p>
          ) : (
            <DataTable columns={utilColumns} data={utilData} pageSize={25} />
          )}
        </>
      )}

      {tab === "pricing" && (
        <>
          <FilterBar
            filters={[
              {
                type: "search",
                label: "HCPCS Code",
                value: hcpcsSearch,
                onChange: setHcpcsSearch,
                placeholder: "e.g. J0129",
              },
            ]}
          />
          {priceData.length > 0 ? (
            <DataTable columns={priceColumns} data={priceData} pageSize={25} />
          ) : (
            <p className="text-slate-500">
              Enter a HCPCS code (4+ characters) to see price trends.
            </p>
          )}
        </>
      )}
    </div>
  );
}
