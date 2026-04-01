"use client";

import { useEffect, useState } from "react";
import DataTable from "@/components/data-table";
import FilterBar from "@/components/filter-bar";
import KpiCard from "@/components/kpi-card";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/format";

interface HospitalFinancial {
  ccn: string;
  facility_name: string;
  provider_state: string;
  hospital_type: string;
  data_year: number;
  cms_overall_rating: number | null;
  total_patient_revenue: number | null;
  operating_margin: number | null;
  cost_to_charge_ratio: number | null;
  total_beds_available: number | null;
  total_discharges: number | null;
  occupancy_rate: number | null;
}

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export default function HospitalComparisonPage() {
  const [hospitals, setHospitals] = useState<HospitalFinancial[]>([]);
  const [year, setYear] = useState(2022);
  const [state, setState] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams({ data_year: String(year), limit: "200" });
    if (state) params.set("state", state);

    fetch(`${API}/hospitals/financial?${params}`)
      .then((r) => r.json())
      .then(setHospitals)
      .catch(() => setHospitals([]))
      .finally(() => setLoading(false));
  }, [year, state]);

  const totalRevenue = hospitals.reduce((s, h) => s + (h.total_patient_revenue || 0), 0);
  const totalDischarges = hospitals.reduce((s, h) => s + (h.total_discharges || 0), 0);
  const avgMargin = hospitals.length
    ? hospitals.reduce((s, h) => s + (h.operating_margin || 0), 0) / hospitals.length
    : 0;

  const columns = [
    { key: "ccn", label: "CCN" },
    { key: "facility_name", label: "Facility Name" },
    { key: "provider_state", label: "State" },
    { key: "hospital_type", label: "Type" },
    {
      key: "cms_overall_rating",
      label: "CMS Rating",
      render: (v: number | null) => (v != null ? `${"★".repeat(v)}${"☆".repeat(5 - v)}` : "N/A"),
    },
    {
      key: "total_patient_revenue",
      label: "Revenue",
      render: (v: number | null) => formatCurrency(v || 0),
    },
    {
      key: "operating_margin",
      label: "Op. Margin",
      render: (v: number | null) => (v != null ? formatPercent(v * 100) : "N/A"),
    },
    {
      key: "total_beds_available",
      label: "Beds",
      render: (v: number | null) => formatNumber(v || 0),
    },
    {
      key: "occupancy_rate",
      label: "Occupancy",
      render: (v: number | null) => (v != null ? formatPercent(v * 100) : "N/A"),
    },
  ];

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-slate-900">Hospital Comparison</h2>

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
          {
            type: "search",
            label: "State",
            value: state,
            onChange: setState,
            placeholder: "e.g. CA",
          },
        ]}
      />

      <div className="grid grid-cols-3 gap-4">
        <KpiCard label="Total Revenue" value={formatCurrency(totalRevenue)} />
        <KpiCard label="Total Discharges" value={formatNumber(totalDischarges)} />
        <KpiCard
          label="Avg Operating Margin"
          value={formatPercent(avgMargin * 100)}
        />
      </div>

      {loading ? (
        <p className="text-slate-500">Loading hospitals...</p>
      ) : (
        <DataTable columns={columns} data={hospitals} pageSize={25} />
      )}
    </div>
  );
}
