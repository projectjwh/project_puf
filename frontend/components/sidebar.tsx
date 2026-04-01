/**
 * Sidebar navigation component.
 */

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/dashboard", label: "National Dashboard" },
  { href: "/providers", label: "Provider Lookup" },
  { href: "/geographic", label: "Geographic Explorer" },
  { href: "/specialties", label: "Specialty Comparison" },
  { href: "/opioid", label: "Opioid Monitor" },
  { href: "/hospitals", label: "Hospital Comparison" },
  { href: "/drugs", label: "Drug Spending" },
  { href: "/postacute", label: "Post-Acute Care" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-screen w-64 flex-col border-r border-slate-200 bg-white">
      <div className="border-b border-slate-200 px-6 py-5">
        <h1 className="text-lg font-bold text-slate-900">Project PUF</h1>
        <p className="text-xs text-slate-500">Public Healthcare Data</p>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`block rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? "bg-blue-50 text-blue-700"
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-slate-200 px-6 py-4">
        <p className="text-xs text-slate-400">v0.1.0 MVP</p>
      </div>
    </aside>
  );
}
