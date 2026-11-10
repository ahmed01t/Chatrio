/**
 * StatCard — tasteskill.dev aligned-figures style
 *
 * Quiet white panel, big tabular figure, small muted label above,
 * subtle trend line below. Colour is spent only on the trend delta.
 */
import React from "react";

export interface StatCardProps {
  title:     string;
  value:     string | number;
  trend?:    string;
  trendType?: "success" | "terracotta" | "warning" | "critical" | "neutral";
  icon?:     React.ReactNode;
  subtitle?: string;
}

const trendColours: Record<NonNullable<StatCardProps["trendType"]>, string> = {
  success:    "text-data-emerald",
  terracotta: "text-accent",
  warning:    "text-data-amber",
  critical:   "text-rose-600",
  neutral:    "text-ink-500",
};

export function StatCard({
  title,
  value,
  trend,
  trendType = "neutral",
  icon,
  subtitle,
}: StatCardProps) {
  return (
    <div className="quiet-panel p-5 card-taste flex flex-col gap-3">
      {/* Label + icon row */}
      <div className="flex items-center justify-between">
        <span className="text-[13px] font-medium text-ink-500">{title}</span>
        {icon && (
          <div className="w-7 h-7 rounded-[8px] bg-canvas-subtle border border-border flex items-center justify-center">
            {icon}
          </div>
        )}
      </div>

      {/* Aligned figure */}
      <span
        className="text-[2rem] leading-none font-bold text-ink-900
                   tabular-nums tracking-tight"
      >
        {value}
      </span>

      {/* Trend / subtitle */}
      {(trend || subtitle) && (
        <div className="flex items-center justify-between pt-2 border-t border-border/60 text-[12px]">
          {trend && (
            <span className={`font-semibold ${trendColours[trendType]}`}>
              {trend}
            </span>
          )}
          {subtitle && (
            <span className="text-ink-400 truncate">{subtitle}</span>
          )}
        </div>
      )}
    </div>
  );
}
