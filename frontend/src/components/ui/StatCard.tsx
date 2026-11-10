import React from "react";
import { Badge } from "./Badge";

export interface StatCardProps {
  title: string;
  value: string | number;
  trend?: string;
  trendType?: "critical" | "warning" | "active" | "success" | "purple" | "neutral";
  icon?: React.ReactNode;
}

export function StatCard({
  title,
  value,
  trend,
  trendType = "neutral",
  icon,
}: StatCardProps) {
  return (
    <div className="bg-obsidian-850/90 border border-obsidian-700/80 rounded-xl p-4 sm:p-5 hover:border-obsidian-600 transition-all shadow-card flex flex-col justify-between">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2.5">
          {icon && (
            <div className="w-8 h-8 rounded-lg bg-obsidian-800 border border-obsidian-700/70 flex items-center justify-center text-obsidian-300">
              {icon}
            </div>
          )}
          <span className="text-2xl sm:text-3xl font-bold tracking-tight text-white font-mono">
            {value}
          </span>
        </div>
        {trend && (
          <Badge variant={trendType} size="sm">
            {trend}
          </Badge>
        )}
      </div>
      <p className="text-xs font-medium text-obsidian-400 capitalize">{title}</p>
    </div>
  );
}
