/**
 * Data Table — sortable, paginated table for displaying tabular data.
 */

"use client";

import { useState } from "react";

interface Column<T> {
  key: keyof T;
  label: string;
  format?: (value: unknown) => string;
  align?: "left" | "right" | "center";
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  pageSize?: number;
  onRowClick?: (row: T) => void;
}

export default function DataTable<T extends Record<string, unknown>>({
  columns,
  data,
  pageSize = 25,
  onRowClick,
}: DataTableProps<T>) {
  const [page, setPage] = useState(0);
  const [sortKey, setSortKey] = useState<keyof T | null>(null);
  const [sortAsc, setSortAsc] = useState(true);

  const sorted = [...data].sort((a, b) => {
    if (!sortKey) return 0;
    const va = a[sortKey];
    const vb = b[sortKey];
    if (va == null) return 1;
    if (vb == null) return -1;
    const cmp = va < vb ? -1 : va > vb ? 1 : 0;
    return sortAsc ? cmp : -cmp;
  });

  const totalPages = Math.ceil(sorted.length / pageSize);
  const pageData = sorted.slice(page * pageSize, (page + 1) * pageSize);

  const handleSort = (key: keyof T) => {
    if (sortKey === key) {
      setSortAsc(!sortAsc);
    } else {
      setSortKey(key);
      setSortAsc(true);
    }
    setPage(0);
  };

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-slate-200">
        <thead className="bg-slate-50">
          <tr>
            {columns.map((col) => (
              <th
                key={String(col.key)}
                onClick={() => handleSort(col.key)}
                className={`cursor-pointer px-4 py-3 text-xs font-medium uppercase tracking-wider text-slate-500 ${
                  col.align === "right" ? "text-right" : "text-left"
                }`}
              >
                {col.label}
                {sortKey === col.key && (sortAsc ? " \u25B2" : " \u25BC")}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {pageData.map((row, i) => (
            <tr
              key={i}
              onClick={() => onRowClick?.(row)}
              className={onRowClick ? "cursor-pointer hover:bg-slate-50" : ""}
            >
              {columns.map((col) => (
                <td
                  key={String(col.key)}
                  className={`px-4 py-3 text-sm text-slate-700 ${
                    col.align === "right" ? "text-right" : "text-left"
                  }`}
                >
                  {col.format
                    ? col.format(row[col.key])
                    : String(row[col.key] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>

      {totalPages > 1 && (
        <div className="flex items-center justify-between border-t border-slate-200 px-4 py-3">
          <p className="text-sm text-slate-500">
            Showing {page * pageSize + 1}-{Math.min((page + 1) * pageSize, sorted.length)} of{" "}
            {sorted.length}
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(Math.max(0, page - 1))}
              disabled={page === 0}
              className="rounded border px-3 py-1 text-sm disabled:opacity-50"
            >
              Previous
            </button>
            <button
              onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
              disabled={page >= totalPages - 1}
              className="rounded border px-3 py-1 text-sm disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
