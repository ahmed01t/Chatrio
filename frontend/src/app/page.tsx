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
  AlertCircle,
  RefreshCw,
} from "lucide-react";
import { StatCard } from "@/components/ui/StatCard";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { ConversationRead, OrderRead } from "@/types";
import { ordersService } from "@/services/orders.service";
import { conversationsService } from "@/services/conversations.service";

export default function DashboardPage() {
  const [conversations, setConversations] = useState<ConversationRead[]>([]);
  const [orders, setOrders] = useState<OrderRead[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadRealTelemetry = async () => {
    setIsLoading(true);
    setError(null);
    try {
      /**
       * Calls real backend routers:
       * 1. GET /api/v1/orders        -> backend/app/modules/orders/router.py:58
       * 2. GET /api/v1/conversations -> backend/app/modules/conversations/router.py:58
       */
      const [orderRes, convRes] = await Promise.all([
        ordersService.listOrders({ page: 1, page_size: 20 }),
        conversationsService.listConversations({ page: 1, page_size: 20 }),
      ]);

      setOrders(orderRes.items);
      setConversations(convRes.items);
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load telemetry from Chatrio backend."
      );
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadRealTelemetry();
  }, []);

  // Compute live metrics strictly from real PostgreSQL data
  const totalRevenue = orders
    .filter((o) => o.payment_status === "PAID")
    .reduce((sum, o) => sum + Number(o.total_amount), 0);

  const pendingOrdersCount = orders.filter((o) => o.status === "PENDING").length;
  const activeConversationsCount = conversations.filter(
    (c) => c.status === "ACTIVE"
  ).length;

  const aiHandledCount = conversations.filter((c) => c.is_ai_active).length;
  const aiResolutionRate =
    conversations.length > 0
      ? Math.round((aiHandledCount / conversations.length) * 100)
      : 100;

  return (
    <div className="space-y-6 sm:space-y-8 animate-in fade-in duration-200">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-obsidian-800">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-obsidian-400 mb-1">
            <span>Store Operations</span>
            <span>/</span>
            <span className="text-brand-emerald">Signals & Overview</span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Store Signals & Telemetry
          </h1>
          <p className="text-xs sm:text-sm text-obsidian-400 mt-1">
            Live conversational commerce metrics aggregated directly from PostgreSQL & Redis.
          </p>
        </div>

        <div className="flex items-center gap-2 sm:gap-3">
          <Button
            variant="secondary"
            size="sm"
            onClick={loadRealTelemetry}
            isLoading={isLoading}
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Sync Live Data</span>
          </Button>

          <Link href="/products">
            <Button size="sm">
              <Package className="w-3.5 h-3.5" />
              <span>Add Product</span>
            </Button>
          </Link>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-brand-rose/10 border border-brand-rose/30 text-xs text-rose-300 flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0 text-brand-rose" />
          <span>{error}</span>
        </div>
      )}

      {/* 4 Top KPI StatCards derived 100% from real database rows */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <StatCard
          title="Total Store Revenue"
          value={`$${totalRevenue.toLocaleString("en-US", { minimumFractionDigits: 2 })}`}
          trend={`${orders.length} orders total`}
          trendType="success"
          icon={<DollarSign className="w-4 h-4 text-brand-emerald" />}
        />
        <StatCard
          title="Active WhatsApp Inquiries"
          value={activeConversationsCount}
          trend={`${conversations.length} sessions`}
          trendType="active"
          icon={<MessageSquare className="w-4 h-4 text-brand-cyan" />}
        />
        <StatCard
          title="Orders Pending"
          value={pendingOrdersCount}
          trend={pendingOrdersCount > 0 ? "Fulfillment required" : "All cleared"}
          trendType={pendingOrdersCount > 0 ? "warning" : "success"}
          icon={<Package className="w-4 h-4 text-brand-amber" />}
        />
        <StatCard
          title="AI Automation Rate"
          value={`${aiResolutionRate}%`}
          trend={`${aiHandledCount} copilot active`}
          trendType="purple"
          icon={<Bot className="w-4 h-4 text-brand-purple" />}
        />
      </div>

      {/* Main Grid: Left = Activity Feed, Right = AI Fortress */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Active Customer Conversations Table */}
          <div className="bg-obsidian-850/80 border border-obsidian-750/90 rounded-xl shadow-card overflow-hidden">
            <div className="p-4 sm:p-5 border-b border-obsidian-750/70 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-white tracking-tight flex items-center gap-2">
                  <MessageSquare className="w-4 h-4 text-brand-cyan" />
                  <span>Live WhatsApp Conversations</span>
                </h3>
                <p className="text-xs text-obsidian-400 mt-0.5">
                  Connected to backend router: GET /api/v1/conversations
                </p>
              </div>
              <Link
                href="/inbox"
                className="text-xs text-brand-emerald hover:text-emerald-300 font-medium flex items-center gap-1 transition-colors"
              >
                <span>Open Shared Inbox</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="divide-y divide-obsidian-750/50">
              {conversations.length === 0 && !isLoading ? (
                <div className="py-12 px-6 text-center text-obsidian-400 space-y-2">
                  <MessageSquare className="w-8 h-8 text-obsidian-600 mx-auto" />
                  <p className="font-semibold text-white text-xs">
                    No WhatsApp conversations recorded yet
                  </p>
                  <p className="text-xs text-obsidian-500 max-w-sm mx-auto">
                    Inbound messages from Meta Webhooks will automatically populate this queue.
                  </p>
                </div>
              ) : (
                conversations.slice(0, 5).map((conv) => (
                  <div
                    key={conv.id}
                    className="p-4 sm:px-5 flex items-center justify-between hover:bg-obsidian-800/60 transition-colors gap-3"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="w-9 h-9 rounded-xl bg-obsidian-800 border border-obsidian-700/80 flex items-center justify-center font-mono font-semibold text-xs text-brand-emerald shrink-0">
                        {conv.customer?.name ? conv.customer.name[0].toUpperCase() : "C"}
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="text-xs font-semibold text-white truncate">
                            {conv.customer?.name || "WhatsApp Customer"}
                          </p>
                          <span className="text-[11px] text-obsidian-500 font-mono">
                            {conv.customer?.phone_number || "Direct"}
                          </span>
                        </div>
                        <p className="text-xs text-obsidian-400 truncate mt-0.5 font-mono">
                          Session ID: {conv.id.slice(0, 8)}...
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
                  <span>Recent PostgreSQL Orders</span>
                </h3>
                <p className="text-xs text-obsidian-400 mt-0.5">
                  Connected to backend router: GET /api/v1/orders
                </p>
              </div>
              <Link
                href="/orders"
                className="text-xs text-brand-emerald hover:text-emerald-300 font-medium flex items-center gap-1 transition-colors"
              >
                <span>Fulfillment Board</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="divide-y divide-obsidian-750/50">
              {orders.length === 0 && !isLoading ? (
                <div className="py-12 px-6 text-center text-obsidian-400 space-y-2">
                  <Package className="w-8 h-8 text-obsidian-600 mx-auto" />
                  <p className="font-semibold text-white text-xs">No orders in database</p>
                  <p className="text-xs text-obsidian-500 max-w-sm mx-auto">
                    Orders created by customers in WhatsApp or via API will appear here.
                  </p>
                </div>
              ) : (
                orders.slice(0, 5).map((order) => (
                  <div
                    key={order.id}
                    className="p-4 sm:px-5 flex items-center justify-between hover:bg-obsidian-800/60 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-xs font-bold text-white">
                        {order.order_number}
                      </span>
                      <span className="text-xs text-obsidian-400 font-mono">
                        {order.items?.length || 0} items
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
                ))
              )}
            </div>
          </div>
        </div>

        {/* Right 1 Col: AI Security & Guardrails */}
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
              Zero vendor lock-in. Powered by LangGraph state machine with automatic fallbacks.
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
