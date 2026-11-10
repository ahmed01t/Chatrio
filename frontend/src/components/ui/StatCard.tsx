import React from "react";
import { Badge } from "./Badge";

export interface StatCardProps {
  title: string;
  value: string | number;
  trend?: string;
  trendType?: "critical" | "warning" | "active" | "success" | "purple" | "neutral" | "terracotta";
  icon?: React.ReactNode;
  subtitle?: string;
}

export function StatCard({
  title,
  value,
  trend,
  trendType = "neutral",
  icon,
  subtitle,
}: StatCardProps) {
  const trendColor =
    trendType === "success"
      ? "text-emerald-600"
      : trendType === "terracotta"
      ? "text-accent"
      : trendType === "warning"
      ? "text-amber-600"
      : trendType === "critical"
      ? "text-rose-600"
      : "text-ink-500";

  return (
    <div className="quiet-panel p-5 card-taste flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-ink-500 tracking-tight">
            {title}
          </span>
          {icon && (
            <div className="w-6 h-6 rounded-lg bg-canvas-subtle border border-border flex items-center justify-center text-ink-600">
              {icon}
            </div>
          )}
        </div>

        <div className="text-2xl sm:text-3xl font-bold tracking-tight text-ink-900">
          {value}
        </div>
      </div>

      <div className="flex items-center justify-between mt-3 pt-2 border-t border-border/60 text-xs">
        {trend && (
          <span className={`font-semibold flex items-center gap-1 ${trendColor}`}>
            {trend}
          </span>
        )}
        {subtitle && (
          <span className="text-[11px] text-ink-400 font-mono truncate">
            {subtitle}
          </span>
        )}
      </div>
    </div>
  );
}
