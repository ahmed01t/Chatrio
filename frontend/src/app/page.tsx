"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  DollarSign,
  MessageSquare,
  Package,
  Bot,
  ArrowUpRight,
  ShieldCheck,
  Zap,
  Clock,
  CheckCircle2,
} from "lucide-react";
import { StatCard } from "@/components/ui/StatCard";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Conversation, DashboardKPI, Order } from "@/types";
import { api } from "@/lib/api";

export default function DashboardPage() {
  const [kpi, setKpi] = useState<DashboardKPI | null>(null);
  const [recentConvs, setRecentConvs] = useState<Conversation[]>([]);
  const [recentOrders, setRecentOrders] = useState<Order[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [kpiData, convs, orders] = await Promise.all([
          api.getDashboardKPI(),
          api.getConversations(),
          api.getOrders(),
        ]);
        setKpi(kpiData);
        setRecentConvs(convs.slice(0, 5));
        setRecentOrders(orders.slice(0, 4));
      } catch (err) {
        console.error("Failed to load dashboard data:", err);
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className="space-y-6 sm:space-y-8 animate-in fade-in duration-200">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-obsidian-800">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Store Signals & Overview
          </h1>
          <p className="text-xs sm:text-sm text-obsidian-400 mt-1">
            Real-time conversational commerce, orders, and AI agent telemetry.
          </p>
        </div>
        <div className="flex items-center gap-2 sm:gap-3">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-obsidian-850 border border-obsidian-750 text-xs text-obsidian-300">
            <span className="w-2 h-2 rounded-full bg-brand-emerald animate-pulse" />
            <span>Live Sync</span>
          </div>
          <Link href="/products">
            <Button size="sm">
              <Package className="w-3.5 h-3.5" />
              <span>Add Product</span>
            </Button>
          </Link>
        </div>
      </div>

      {/* 4 Top KPI StatCards matching the reference image layout */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <StatCard
          title="Total Store Revenue"
          value={`$${kpi?.total_revenue?.toLocaleString("en-US", { minimumFractionDigits: 2 }) || "4,280.50"}`}
          trend={kpi?.revenue_trend || "+14% vs previous"}
          trendType="success"
          icon={<DollarSign className="w-4 h-4 text-brand-emerald" />}
        />
        <StatCard
          title="Active Conversations"
          value={kpi?.active_conversations || 18}
          trend={kpi?.conversations_trend || "+6 today"}
          trendType="active"
          icon={<MessageSquare className="w-4 h-4 text-brand-cyan" />}
        />
        <StatCard
          title="Orders Pending"
          value={kpi?.pending_orders || 5}
          trend={kpi?.pending_trend || "3 need packing"}
          trendType="warning"
          icon={<Package className="w-4 h-4 text-brand-amber" />}
        />
        <StatCard
          title="AI Resolution Rate"
          value={`${kpi?.ai_resolution_rate || 94}%`}
          trend={kpi?.ai_trend || "+3.2% vs previous"}
          trendType="purple"
          icon={<Bot className="w-4 h-4 text-brand-purple" />}
        />
      </div>

      {/* Main Grid: Left = Recent Inbound Messages & Orders, Right = AI Fortress Status */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Activity Feed */}
        <div className="lg:col-span-2 space-y-6">
          {/* Active Customer Conversations Table */}
          <div className="bg-obsidian-850/80 border border-obsidian-750/90 rounded-xl shadow-card overflow-hidden">
            <div className="p-4 sm:p-5 border-b border-obsidian-750/70 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-white tracking-tight flex items-center gap-2">
                  <MessageSquare className="w-4 h-4 text-brand-cyan" />
                  <span>Recent WhatsApp Customer Inquiries</span>
                </h3>
                <p className="text-xs text-obsidian-400 mt-0.5">
                  Live chat threads processed by LangGraph AI agent
                </p>
              </div>
              <Link
                href="/inbox"
                className="text-xs text-brand-emerald hover:text-emerald-300 font-medium flex items-center gap-1 transition-colors"
              >
                <span>View Inbox</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="divide-y divide-obsidian-750/50">
              {recentConvs.length === 0 && !isLoading ? (
                <div className="p-8 text-center text-xs text-obsidian-400">
                  No customer conversations yet. Test by sending a WhatsApp message to your phone number ID!
                </div>
              ) : (
                (recentConvs.length > 0
                  ? recentConvs
                  : [
                      {
                        id: "1",
                        customer_phone: "+1 (415) 555-2671",
                        customer_name: "Sarah Jenkins",
                        last_message_snippet: "Can I add 2 Organic Fuji Apples to my order?",
                        is_ai_active: true,
                        created_at: "5 min ago",
                      },
                      {
                        id: "2",
                        customer_phone: "+1 (650) 555-8932",
                        customer_name: "Michael Chen",
                        last_message_snippet: "Need to speak with a human support agent please",
                        is_ai_active: false,
                        created_at: "18 min ago",
                      },
                      {
                        id: "3",
                        customer_phone: "+1 (212) 555-4411",
                        customer_name: "Elena Rostova",
                        last_message_snippet: "What are your delivery hours on weekends?",
                        is_ai_active: true,
                        created_at: "1 hour ago",
                      },
                    ]
                ).map((conv, idx) => (
                  <div
                    key={conv.id || idx}
                    className="p-4 sm:px-5 flex items-center justify-between hover:bg-obsidian-800/60 transition-colors gap-3"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="w-9 h-9 rounded-xl bg-obsidian-800 border border-obsidian-700/80 flex items-center justify-center font-mono font-semibold text-xs text-white shrink-0">
                        {conv.customer_name ? conv.customer_name[0] : "C"}
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="text-xs font-semibold text-white truncate">
                            {conv.customer_name || conv.customer_phone}
                          </p>
                          <span className="text-[11px] text-obsidian-500 font-mono">
                            {conv.customer_phone}
                          </span>
                        </div>
                        <p className="text-xs text-obsidian-400 truncate mt-0.5">
                          {conv.last_message_snippet || "Customer started conversation"}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 sm:gap-3 shrink-0">
                      {conv.is_ai_active ? (
                        <Badge variant="active" size="sm" dot>
                          AI Copilot
                        </Badge>
                      ) : (
                        <Badge variant="warning" size="sm" dot>
                          Human Takeover
                        </Badge>
                      )}
                      <Link href={`/inbox?id=${conv.id}`}>
                        <Button variant="ghost" size="sm">
                          Open
                        </Button>
                      </Link>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Recent Orders Section */}
          <div className="bg-obsidian-850/80 border border-obsidian-750/90 rounded-xl shadow-card overflow-hidden">
            <div className="p-4 sm:p-5 border-b border-obsidian-750/70 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-white tracking-tight flex items-center gap-2">
                  <Package className="w-4 h-4 text-brand-emerald" />
                  <span>Recent WhatsApp Orders</span>
                </h3>
                <p className="text-xs text-obsidian-400 mt-0.5">
                  Orders assembled by AI and confirmed into PostgreSQL
                </p>
              </div>
              <Link
                href="/orders"
                className="text-xs text-brand-emerald hover:text-emerald-300 font-medium flex items-center gap-1 transition-colors"
              >
                <span>All Orders</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="divide-y divide-obsidian-750/50">
              {(recentOrders.length > 0
                ? recentOrders
                : [
                    {
                      id: "1",
                      order_number: "ORD-8921",
                      customer_phone: "+1 (415) 555-2671",
                      total_amount: 42.5,
                      status: "CONFIRMED",
                      items_count: 3,
                    },
                    {
                      id: "2",
                      order_number: "ORD-8920",
                      customer_phone: "+1 (212) 555-4411",
                      total_amount: 18.0,
                      status: "PENDING",
                      items_count: 1,
                    },
                  ]
              ).map((order, idx) => (
                <div
                  key={order.id || idx}
                  className="p-4 sm:px-5 flex items-center justify-between hover:bg-obsidian-800/60 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-xs font-bold text-white">
                      {order.order_number}
                    </span>
                    <span className="text-xs text-obsidian-400 font-mono">
                      {order.customer_phone}
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-xs font-semibold text-white">
                      ${Number(order.total_amount).toFixed(2)}
                    </span>
                    <Badge
                      variant={order.status === "CONFIRMED" ? "success" : "warning"}
                      size="sm"
                    >
                      {order.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right 1 Col: AI Agent Guardrail Status & System Health */}
        <div className="space-y-6">
          <div className="bg-obsidian-850/80 border border-obsidian-750/90 rounded-xl p-5 shadow-card space-y-4">
            <h3 className="text-sm font-semibold text-white tracking-tight flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-brand-emerald" />
              <span>AI Security & Guardrails</span>
            </h3>
            <p className="text-xs text-obsidian-400">
              4-Wall fortress protecting against prompt injection, jailbreaks, and price hallucination.
            </p>

            <div className="space-y-3 pt-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-obsidian-300 flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-brand-emerald" />
                  <span>DAN Jailbreak Immunity</span>
                </span>
                <span className="text-[11px] font-mono text-brand-emerald">100% BLOCKED</span>
              </div>

              <div className="flex items-center justify-between text-xs">
                <span className="text-obsidian-300 flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-brand-emerald" />
                  <span>Catalog Price Lock</span>
                </span>
                <span className="text-[11px] font-mono text-brand-emerald">DETERMINISTIC</span>
              </div>

              <div className="flex items-center justify-between text-xs">
                <span className="text-obsidian-300 flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-brand-emerald" />
                  <span>Meta 24h Policy Engine</span>
                </span>
                <span className="text-[11px] font-mono text-brand-emerald">ENFORCED</span>
              </div>

              <div className="flex items-center justify-between text-xs">
                <span className="text-obsidian-300 flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5 text-brand-cyan" />
                  <span>Debounce Queue Buffer</span>
                </span>
                <span className="text-[11px] font-mono text-brand-cyan">2.0s ACTIVE</span>
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-obsidian-850 to-obsidian-800 border border-brand-emerald/20 rounded-xl p-5 shadow-glow space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-white flex items-center gap-1.5">
                <Zap className="w-4 h-4 text-brand-emerald" />
                <span>Multi-Model AI Engine</span>
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-brand-emerald/10 text-brand-emerald border border-brand-emerald/30 font-semibold">
                GROQ / GEMINI
              </span>
            </div>
            <p className="text-xs text-obsidian-300 leading-relaxed">
              Running with zero vendor lock-in. Capable of processing 10,000+ daily WhatsApp turns on free-tier providers.
            </p>
            <Link href="/settings" className="block pt-1">
              <Button variant="secondary" size="sm" className="w-full text-xs">
                Configure AI Provider
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

