/**
 * Filter bar — reusable horizontal filter strip with dropdowns and search.
 */

"use client";

interface FilterOption {
  value: string;
  label: string;
}

interface FilterBarProps {
  filters: {
    key: string;
    label: string;
    type: "select" | "search";
    options?: FilterOption[];
    placeholder?: string;
  }[];
  values: Record<string, string>;
  onChange: (key: string, value: string) => void;
}

export default function FilterBar({ filters, values, onChange }: FilterBarProps) {
  return (
    <div className="flex flex-wrap items-center gap-4 rounded-lg border border-slate-200 bg-white px-4 py-3">
      {filters.map((filter) => (
        <div key={filter.key} className="flex items-center gap-2">
          <label className="text-sm font-medium text-slate-600">{filter.label}:</label>
          {filter.type === "select" ? (
            <select
              value={values[filter.key] || ""}
              onChange={(e) => onChange(filter.key, e.target.value)}
              className="rounded border border-slate-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
            >
              <option value="">All</option>
              {filter.options?.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          ) : (
            <input
              type="text"
              value={values[filter.key] || ""}
              onChange={(e) => onChange(filter.key, e.target.value)}
              placeholder={filter.placeholder || "Search..."}
              className="rounded border border-slate-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
            />
          )}
        </div>
      ))}
    </div>
  );
}
