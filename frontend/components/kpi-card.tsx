/**
 * KPI Card — displays a single metric with label, value, and optional change indicator.
 */

interface KpiCardProps {
  label: string;
  value: string;
  change?: number | null;
  changeLabel?: string;
  icon?: string;
}

export default function KpiCard({ label, value, change, changeLabel, icon }: KpiCardProps) {
  const changeColor = change == null ? "" : change > 0 ? "text-red-600" : "text-green-600";
  const changeArrow = change == null ? "" : change > 0 ? "\u2191" : "\u2193";

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-slate-500">{label}</p>
        {icon && <span className="text-2xl">{icon}</span>}
      </div>
      <p className="mt-2 text-3xl font-bold text-slate-900">{value}</p>
      {change != null && (
        <p className={`mt-1 text-sm ${changeColor}`}>
          {changeArrow} {Math.abs(change).toFixed(1)}% {changeLabel || "vs prior year"}
        </p>
      )}
    </div>
  );
}
