"use client";

import React, { useState } from "react";
import {
  Activity,
  AlertTriangle,
  AlertOctagon,
  Clock,
  Sparkles,
  Zap,
} from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { StatCard } from "@/components/ui/StatCard";

interface SignalItem {
  id: string;
  title: string;
  description: string;
  model: string;
  timeAgo: string;
  severity: "critical" | "warning" | "active" | "neutral";
  metricLabel: string;
  metricValue: string;
  status: "Active" | "Acknowledged" | "Resolved";
  baseline: string;
  threshold: string;
  duration: string;
}

const SIGNALS_DATA: SignalItem[] = [
  {
    id: "sig-1",
    title: "Error rate spike - gpt-4o-mini",
    description: "Errors rose 3.4x between 2:00-4:00 PM UTC during high message burst.",
    model: "gpt-4o-mini",
    timeAgo: "12 min ago",
    severity: "critical",
    metricLabel: "Error rate",
    metricValue: "1.42%",
    status: "Active",
    baseline: "0.41%",
    threshold: "> 0.90%",
    duration: "42 min",
  },
  {
    id: "sig-2",
    title: "Cost acceleration - llama-3.3-70b",
    description: "Token spend is tracking 18% above 7-day median due to deep catalog searches.",
    model: "llama-3.3-70b",
    timeAgo: "1h ago",
    severity: "warning",
    metricLabel: "Cost delta",
    metricValue: "+18%",
    status: "Active",
    baseline: "$0.02 / turn",
    threshold: "> +15%",
    duration: "1h 15m",
  },
  {
    id: "sig-3",
    title: "p95 latency breach - LangGraph Catalog Tool",
    description: "Catalog RAG retrieval held above 2.0s for 28 minutes during batch stock sync.",
    model: "LangGraph Tools",
    timeAgo: "26 min ago",
    severity: "warning",
    metricLabel: "p95 latency",
    metricValue: "2.10s",
    status: "Active",
    baseline: "0.85s",
    threshold: "> 2.00s",
    duration: "28 min",
  },
  {
    id: "sig-4",
    title: "Prompt injection attempt detected - Guardrail Wall 1",
    description: "Input guardrail intercepted delimiter escape </customer_input> and blocked session.",
    model: "Guardrail Firewall",
    timeAgo: "54 min ago",
    severity: "critical",
    metricLabel: "Refusal rate",
    metricValue: "100%",
    status: "Acknowledged",
    baseline: "100%",
    threshold: "< 100%",
    duration: "Instant",
  },
];

export default function AnalyticsPage() {
  const [selectedSignal, setSelectedSignal] = useState<SignalItem>(SIGNALS_DATA[0]);
  const [filterSeverity, setFilterSeverity] = useState<string>("ALL");

  const filteredSignals = SIGNALS_DATA.filter((s) => {
    if (filterSeverity === "ALL") return true;
    return s.severity.toUpperCase() === filterSeverity;
  });

  return (
    <div className="space-y-6 animate-in fade-in duration-150">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-obsidian-800">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-obsidian-400 mb-1">
            <span>AI Ops</span>
            <span>/</span>
            <span className="text-brand-emerald">Signals & Telemetry</span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Activity className="w-6 h-6 text-brand-emerald" />
            <span>AI Agent Telemetry & Invariants</span>
          </h1>
          <p className="text-xs sm:text-sm text-obsidian-400 mt-1">
            Anomalies, guardrail trips, and model latency metrics across LangGraph pipelines.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-obsidian-850 border border-obsidian-750 text-xs text-obsidian-300 font-mono">
            <span className="w-2 h-2 rounded-full bg-brand-emerald animate-pulse" />
            <span>Telemetry: Live</span>
          </div>
        </div>
      </div>

      {/* Top Stat Cards matching user reference */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <StatCard
          title="Active Signals"
          value="4"
          trend="+2 vs previous"
          trendType="active"
          icon={<Zap className="w-4 h-4 text-brand-cyan" />}
        />
        <StatCard
          title="Critical Alerts"
          value="2"
          trend="+1 vs previous"
          trendType="critical"
          icon={<AlertOctagon className="w-4 h-4 text-brand-rose" />}
        />
        <StatCard
          title="Acknowledged"
          value="1"
          trend="-1 vs previous"
          trendType="warning"
          icon={<AlertTriangle className="w-4 h-4 text-brand-amber" />}
        />
        <StatCard
          title="Resolved Today"
          value="8"
          trend="+4 vs previous"
          trendType="success"
          icon={<Sparkles className="w-4 h-4 text-brand-emerald" />}
        />
      </div>

      {/* Filter Pill Toolbar */}
      <div className="flex items-center gap-2 bg-obsidian-900 p-1.5 rounded-xl border border-obsidian-750/70 w-fit">
        {["ALL", "CRITICAL", "WARNING"].map((sev) => (
          <button
            key={sev}
            onClick={() => setFilterSeverity(sev)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              filterSeverity === sev
                ? "bg-obsidian-800 text-white border border-obsidian-650 font-semibold"
                : "text-obsidian-400 hover:text-white"
            }`}
          >
            {sev}
          </button>
        ))}
      </div>

      {/* Split View: Left = Signal List, Right = Signal Inspector matching reference */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Signals List */}
        <div className="lg:col-span-2 space-y-3">
          {filteredSignals.map((sig) => {
            const isSelected = selectedSignal.id === sig.id;
            return (
              <div
                key={sig.id}
                onClick={() => setSelectedSignal(sig)}
                className={`p-4 rounded-xl border transition-all cursor-pointer flex items-center justify-between gap-4 ${
                  isSelected
                    ? "bg-obsidian-800 border-obsidian-600 shadow-card"
                    : "bg-obsidian-850/80 border-obsidian-750/80 hover:bg-obsidian-800/60"
                }`}
              >
                <div className="flex items-start gap-3.5 min-w-0">
                  <div
                    className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 mt-0.5 ${
                      sig.severity === "critical"
                        ? "bg-red-500/10 border border-red-500/30 text-red-400"
                        : "bg-amber-500/10 border border-amber-500/30 text-amber-400"
                    }`}
                  >
                    {sig.severity === "critical" ? (
                      <AlertOctagon className="w-4 h-4" />
                    ) : (
                      <AlertTriangle className="w-4 h-4" />
                    )}
                  </div>
                  <div className="min-w-0">
                    <h4 className="text-xs sm:text-sm font-semibold text-white tracking-tight truncate">
                      {sig.title}
                    </h4>
                    <p className="text-xs text-obsidian-400 mt-0.5 line-clamp-1">
                      {sig.description}
                    </p>
                    <div className="flex items-center gap-2 mt-2 text-[11px] font-mono text-obsidian-500">
                      <span>{sig.model}</span>
                      <span>•</span>
                      <span>{sig.timeAgo}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-4 shrink-0">
                  {/* Metric Display */}
                  <div className="text-right">
                    <span className="text-[10px] uppercase font-mono text-obsidian-500 block">
                      {sig.metricLabel}
                    </span>
                    <span className="text-sm font-bold font-mono text-white">
                      {sig.metricValue}
                    </span>
                  </div>

                  {/* Sparkline Visual Simulation */}
                  <div className="hidden sm:block w-20 h-8">
                    <svg className="w-full h-full overflow-visible" viewBox="0 0 80 32">
                      <path
                        d="M 0 25 Q 20 20, 35 22 T 60 5 T 80 28"
                        fill="none"
                        stroke={sig.severity === "critical" ? "#EF4444" : "#F59E0B"}
                        strokeWidth="2"
                        strokeLinecap="round"
                      />
                    </svg>
                  </div>

                  <Badge
                    variant={
                      sig.status === "Active"
                        ? "active"
                        : sig.status === "Acknowledged"
                        ? "warning"
                        : "success"
                    }
                    size="sm"
                  >
                    {sig.status}
                  </Badge>
                </div>
              </div>
            );
          })}
        </div>

        {/* Right 1 Col: Inspector matching reference card */}
        <div className="bg-obsidian-850/90 border border-obsidian-750/90 rounded-xl p-5 shadow-card space-y-5">
          <div className="space-y-2 pb-4 border-b border-obsidian-750/70">
            <h3 className="text-sm font-bold text-white tracking-tight">
              {selectedSignal.title}
            </h3>
            <div className="flex items-center gap-2">
              <Badge variant={selectedSignal.severity} size="sm">
                {selectedSignal.severity.toUpperCase()}
              </Badge>
              <Badge variant="active" size="sm">
                {selectedSignal.status}
              </Badge>
            </div>
          </div>

          {/* Overview Grid */}
          <div>
            <h4 className="text-[11px] uppercase font-bold tracking-wider font-mono text-obsidian-400 mb-3">
              Overview
            </h4>
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 rounded-lg bg-obsidian-900 border border-obsidian-750">
                <span className="text-[10px] font-mono text-obsidian-500 uppercase block">
                  Current
                </span>
                <span className="text-base font-bold font-mono text-white">
                  {selectedSignal.metricValue}
                </span>
              </div>
              <div className="p-3 rounded-lg bg-obsidian-900 border border-obsidian-750">
                <span className="text-[10px] font-mono text-obsidian-500 uppercase block">
                  Baseline
                </span>
                <span className="text-base font-bold font-mono text-white">
                  {selectedSignal.baseline}
                </span>
              </div>
              <div className="p-3 rounded-lg bg-obsidian-900 border border-obsidian-750">
                <span className="text-[10px] font-mono text-obsidian-500 uppercase block">
                  Threshold
                </span>
                <span className="text-base font-bold font-mono text-amber-400">
                  {selectedSignal.threshold}
                </span>
              </div>
              <div className="p-3 rounded-lg bg-obsidian-900 border border-obsidian-750">
                <span className="text-[10px] font-mono text-obsidian-500 uppercase block">
                  Duration
                </span>
                <span className="text-base font-bold font-mono text-white">
                  {selectedSignal.duration}
                </span>
              </div>
            </div>
          </div>

          {/* Detailed Wave Chart */}
          <div className="space-y-2">
            <h4 className="text-[11px] uppercase font-bold tracking-wider font-mono text-obsidian-400">
              Metric Trend Timeline
            </h4>
            <div className="h-32 bg-obsidian-900 border border-obsidian-750 rounded-xl p-3 flex flex-col justify-between relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-t from-red-500/10 to-transparent pointer-events-none" />
              <svg className="w-full h-full overflow-visible" viewBox="0 0 200 80">
                <path
                  d="M 0 60 Q 50 50, 90 55 T 140 15 T 200 65"
                  fill="none"
                  stroke="#EF4444"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                />
              </svg>
              <div className="flex justify-between text-[10px] font-mono text-obsidian-500 z-10">
                <span>-60 min</span>
                <span>Now</span>
              </div>
            </div>
          </div>

          {/* Action Resolution */}
          <div className="pt-2 border-t border-obsidian-750/70 text-xs text-obsidian-400 flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-obsidian-500" />
            <span>Monitored continuously via Redis & FastAPI event loop.</span>
          </div>
        </div>
      </div>
    </div>
  );
}

