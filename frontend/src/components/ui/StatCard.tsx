/**
 * StatCard — tasteskill.dev aligned-figures style, dark-mode aware
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
  success:    "#16A34A",
  terracotta: "var(--action)",
  warning:    "#D97706",
  critical:   "#E11D48",
  neutral:    "var(--ink-5)",
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
      {/* Label + icon */}
      <div className="flex items-center justify-between">
        <span
          className="text-[13px] font-medium"
          style={{ color: "var(--ink-5)" }}
        >
          {title}
        </span>
        {icon && (
          <div
            className="w-7 h-7 rounded-[8px] flex items-center justify-center"
            style={{
              backgroundColor: "var(--g-subtle)",
              border: "1px solid var(--line)",
            }}
          >
            {icon}
          </div>
        )}
      </div>

      {/* Aligned figure */}
      <span
        className="text-[2rem] leading-none font-bold tabular-nums tracking-tight"
        style={{ color: "var(--ink)" }}
      >
        {value}
      </span>

      {/* Trend / subtitle */}
      {(trend || subtitle) && (
        <div
          className="flex items-center justify-between gap-2 pt-2 text-[12px] min-w-0"
          style={{ borderTop: "1px solid var(--line-s)" }}
        >
          {trend && (
            <span
              className="font-semibold shrink-0"
              style={{ color: trendColours[trendType] }}
            >
              {trend}
            </span>
          )}
          {subtitle && (
            <span className="truncate text-right" style={{ color: "var(--ink-6)" }} title={subtitle}>
              {subtitle}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
