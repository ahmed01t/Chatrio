"use client";

/**
 * Chatrio AI Agent Telemetry & Invariants Monitor.
 *
 * Implements design-taste-frontend standards:
 * - Quiet panels, aligned figures, colour spent on data
 * - Warm white canvas (#FAF8F5) with terracotta (#EA580C) data highlights
 * - Real-time signal monitoring with SVG sparklines and slide-over event inspector
 */

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
import { Button } from "@/components/ui/Button";
import { StatCard } from "@/components/ui/StatCard";

interface SignalItem {
  id: string;
  title: string;
  description: string;
  model: string;
  timeAgo: string;
  severity: "critical" | "warning" | "active" | "neutral" | "terracotta";
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
    severity: "terracotta",
    metricLabel: "p95 latency",
    metricValue: "2.10s",
    status: "Active",
    baseline: "0.85s",
    threshold: "> 2.00s",
    duration: "28 min",
  },
  {
    id: "sig-4",
    title: "Prompt injection attempt blocked - Guardrail Wall 1",
    description: "Input guardrail intercepted delimiter escape </customer_input> and isolated session.",
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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-border">
        <div>
          <div className="text-xs font-semibold uppercase tracking-wider text-accent mb-1 font-mono">
            AI Operations &bull; Signals
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-ink-900 flex items-center gap-2.5">
            AI Agent Telemetry &amp; Invariants
          </h1>
          <p className="text-xs sm:text-sm text-ink-500 mt-1">
            Anomalies, guardrail trips, and model latency metrics across LangGraph pipelines.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white border border-border text-xs text-ink-700 font-mono shadow-sm">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>Telemetry: Live</span>
          </div>
        </div>
      </div>

      {/* Top 4 Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Active Signals"
          value="4"
          trend="+2 vs previous"
          trendType="terracotta"
          subtitle="Model and queue events"
          icon={<Activity className="w-4 h-4 text-accent" />}
        />
        <StatCard
          title="Critical Invariants"
          value="2"
          trend="+1 vs previous"
          trendType="critical"
          subtitle="Tripped guardrails"
          icon={<AlertOctagon className="w-4 h-4 text-rose-600" />}
        />
        <StatCard
          title="Acknowledged"
          value="1"
          trend="-1 vs previous"
          trendType="warning"
          subtitle="Under staff review"
          icon={<Clock className="w-4 h-4 text-amber-600" />}
        />
        <StatCard
          title="Resolved Today"
          value="3"
          trend="+3 vs previous"
          trendType="success"
          subtitle="Autonomous recovery"
          icon={<Sparkles className="w-4 h-4 text-emerald-600" />}
        />
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs text-ink-500 font-mono mr-2">Filter Severity:</span>
        {["ALL", "CRITICAL", "WARNING", "TERRACOTTA"].map((sev) => (
          <button
            key={sev}
            onClick={() => setFilterSeverity(sev)}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
              filterSeverity === sev
                ? "bg-white text-ink-900 border border-border shadow-sm"
                : "text-ink-500 hover:text-ink-900 bg-canvas-subtle"
            }`}
          >
            {sev}
          </button>
        ))}
        <span className="text-xs text-ink-400 font-mono ml-auto">
          {filteredSignals.length} signals match filters
        </span>
      </div>

      {/* Main Grid: Signals List (Left) + Detail Inspector (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Signals List Rows */}
        <div className="lg:col-span-8 space-y-3">
          {filteredSignals.map((sig) => {
            const isSelected = selectedSignal.id === sig.id;
            return (
              <div
                key={sig.id}
                onClick={() => setSelectedSignal(sig)}
                className={`quiet-panel p-4 cursor-pointer card-taste transition-all ${
                  isSelected
                    ? "border-accent ring-1 ring-accent bg-white shadow-elevated"
                    : "hover:bg-canvas-subtle"
                }`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-3 min-w-0">
                    <div className="mt-0.5">
                      {sig.severity === "critical" ? (
                        <AlertOctagon className="w-5 h-5 text-rose-600" />
                      ) : sig.severity === "warning" ? (
                        <AlertTriangle className="w-5 h-5 text-amber-600" />
                      ) : (
                        <Activity className="w-5 h-5 text-accent" />
                      )}
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <h4 className="text-sm font-bold text-ink-900 truncate">{sig.title}</h4>
                        <Badge
                          variant={sig.severity as any}
                          size="sm"
                        >
                          {sig.severity.toUpperCase()}
                        </Badge>
                      </div>
                      <p className="text-xs text-ink-500 mt-1 line-clamp-1">{sig.description}</p>
                      <div className="flex items-center gap-3 mt-2 text-[11px] font-mono text-ink-400">
                        <span>Model: {sig.model}</span>
                        <span>&bull;</span>
                        <span>{sig.timeAgo}</span>
                      </div>
                    </div>
                  </div>

                  {/* Sparkline & Metric on the Right */}
                  <div className="text-right shrink-0">
                    <span className="text-[10px] font-mono text-ink-400 block">{sig.metricLabel}</span>
                    <span className="text-base font-bold text-ink-900 font-mono block">
                      {sig.metricValue}
                    </span>
                    <div className="w-20 h-7 mt-1 ml-auto">
                      <svg viewBox="0 0 64 24" fill="none" className="w-full h-full">
                        <path
                          d={
                            sig.severity === "critical"
                              ? "M2 18 Q 16 20, 24 14 T 44 4 T 62 10"
                              : "M2 16 Q 16 18, 24 10 T 44 8 T 62 6"
                          }
                          stroke={sig.severity === "critical" ? "#E11D48" : "#EA580C"}
                          strokeWidth="2"
                          strokeLinecap="round"
                        />
                      </svg>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Right Column: Signal Inspector Card */}
        <div className="lg:col-span-4">
          <div className="quiet-panel p-5 card-taste sticky top-20 space-y-4">
            <div className="pb-3 border-b border-border">
              <span className="text-xs font-mono text-ink-400 block mb-1">Signal Inspector</span>
              <h3 className="text-base font-bold text-ink-900">{selectedSignal.title}</h3>
              <div className="flex items-center gap-2 mt-2">
                <Badge variant={selectedSignal.severity as any} size="sm">
                  {selectedSignal.severity.toUpperCase()}
                </Badge>
                <Badge variant="neutral" size="sm">
                  {selectedSignal.status}
                </Badge>
              </div>
            </div>

            {/* Overview Metrics */}
            <div className="grid grid-cols-2 gap-3 py-2">
              <div className="p-3 rounded-xl bg-canvas-subtle border border-border">
                <span className="text-[11px] text-ink-400 font-mono block">Current Value</span>
                <span className="text-lg font-bold text-ink-900 font-mono">
                  {selectedSignal.metricValue}
                </span>
              </div>
              <div className="p-3 rounded-xl bg-canvas-subtle border border-border">
                <span className="text-[11px] text-ink-400 font-mono block">Baseline</span>
                <span className="text-lg font-bold text-ink-900 font-mono">
                  {selectedSignal.baseline}
                </span>
              </div>
              <div className="p-3 rounded-xl bg-canvas-subtle border border-border">
                <span className="text-[11px] text-ink-400 font-mono block">Threshold</span>
                <span className="text-xs font-bold text-rose-600 font-mono">
                  {selectedSignal.threshold}
                </span>
              </div>
              <div className="p-3 rounded-xl bg-canvas-subtle border border-border">
                <span className="text-[11px] text-ink-400 font-mono block">Duration</span>
                <span className="text-xs font-bold text-ink-900 font-mono">
                  {selectedSignal.duration}
                </span>
              </div>
            </div>

            {/* Event Description */}
            <div className="p-3.5 rounded-xl bg-canvas-warm/50 border border-border text-xs text-ink-700 leading-relaxed">
              <span className="font-bold text-ink-900 block mb-1">Diagnostic Log:</span>
              <p>{selectedSignal.description}</p>
            </div>

            {/* Action buttons */}
            <div className="pt-2 flex gap-2">
              <Button size="sm" className="flex-1">
                Acknowledge Signal
              </Button>
              <Button variant="secondary" size="sm">
                Ignore
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
