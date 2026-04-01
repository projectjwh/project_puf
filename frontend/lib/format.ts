/**
 * Formatting utilities for display values.
 */

export function formatCurrency(value: number | null | undefined): string {
  if (value == null) return "N/A";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatNumber(value: number | null | undefined): string {
  if (value == null) return "N/A";
  return new Intl.NumberFormat("en-US").format(value);
}

export function formatPercent(value: number | null | undefined, decimals = 1): string {
  if (value == null) return "N/A";
  return `${value.toFixed(decimals)}%`;
}

export function formatCompact(value: number | null | undefined): string {
  if (value == null) return "N/A";
  if (Math.abs(value) >= 1e9) return `$${(value / 1e9).toFixed(1)}B`;
  if (Math.abs(value) >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
  if (Math.abs(value) >= 1e3) return `$${(value / 1e3).toFixed(0)}K`;
  return formatCurrency(value);
}
