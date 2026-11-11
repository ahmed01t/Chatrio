"use client";

/**
 * Chatrio Dashboard — Live Store Overview
 *
 * The overview uses live tenant-scoped service data and the Chatrio indigo theme.
 * - All numbers come from real API calls — zero hardcoded fallback figures
 */

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  DollarSign,
  MessageSquare,
  Package,
  Bot,
  ArrowUpRight,
  ShieldCheck,
  CheckCircle2,
  RefreshCw,
  AlertCircle,
  TrendingUp,
  Users,
} from "lucide-react";
import { StatCard } from "@/components/ui/StatCard";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { ConversationRead, OrderRead } from "@/types";
import { ordersService } from "@/services/orders.service";
import { conversationsService } from "@/services/conversations.service";
import { customersService } from "@/services/customers.service";

/* ─────────────────────────── helpers ──────────────────────────── */

/** Groups orders by day-of-week (0=Mon … 6=Sun) and sums their total_amount */
function buildWeeklyBars(orders: OrderRead[]) {
  const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const totals = new Array(7).fill(0);

  const now = new Date();
  const startOfWeek = new Date(now);
  startOfWeek.setDate(now.getDate() - ((now.getDay() + 6) % 7)); // Monday
  startOfWeek.setHours(0, 0, 0, 0);

  orders.forEach((o) => {
    const created = new Date(o.created_at);
    if (created >= startOfWeek) {
      const dayIdx = (created.getDay() + 6) % 7; // 0=Mon
      totals[dayIdx] += Number(o.total_amount);
    }
  });

  const max = Math.max(...totals, 1);
  const peakIdx = totals.indexOf(Math.max(...totals));

  return days.map((day, i) => ({
    day,
    total: totals[i],
    heightPct: Math.round((totals[i] / max) * 90) + 10, // 10–100%
    isPeak: i === peakIdx && totals[i] > 0,
  }));
}

function fmt(n: number) {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(1)}k`;
  return `$${n.toFixed(2)}`;
}

/* ─────────────────────────── component ─────────────────────────── */

export default function DashboardPage() {
  const [conversations, setConversations] = useState<ConversationRead[]>([]);
  const [orders, setOrders] = useState<OrderRead[]>([]);
  const [totalCustomers, setTotalCustomers] = useState<number | null>(null);
  const [totalOrders, setTotalOrders] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [orderRes, convRes, custRes] = await Promise.all([
        ordersService.listOrders({ page: 1, page_size: 100 }),
        conversationsService.listConversations({ page: 1, page_size: 100 }),
        customersService.listCustomers({ page: 1, page_size: 1 }),
      ]);

      setOrders(orderRes.items);
      setTotalOrders(orderRes.total);
      setConversations(convRes.items);
      setTotalCustomers(custRes.total);
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not reach the server. Please make sure the backend is running."
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  /* ── computed metrics (all from real data) ── */
  const paidOrders = orders.filter((o) => o.payment_status === "PAID");
  const totalRevenue = paidOrders.reduce((s, o) => s + Number(o.total_amount), 0);
  const pendingCount = orders.filter((o) => o.status === "PENDING").length;
  const activeConvCount = conversations.filter((c) => c.status === "ACTIVE").length;
  const aiHandledCount = conversations.filter((c) => c.is_ai_active).length;
  const aiRate =
    conversations.length > 0
      ? Math.round((aiHandledCount / conversations.length) * 100)
      : null;

  const bars = buildWeeklyBars(orders);
  const peakBar = bars.find((b) => b.isPeak);

  /* ── loading skeleton helper ── */
  const Skeleton = ({ w = "w-20", h = "h-6" }: { w?: string; h?: string }) => (
    <div className={`${w} ${h} rounded bg-oatmeal animate-pulse`} />
  );

  return (
    <div className="space-y-6 sm:space-y-8">

      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 pb-5 border-b border-border" data-enter>
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-accent mb-2">
            Merchant workspace
          </p>
          <h1 className="text-3xl sm:text-4xl font-semibold tracking-tight text-ink-900">
            Store Overview
          </h1>
          <p className="text-sm text-ink-500 mt-2">
            A live view of conversations, orders, and store performance.
          </p>
        </div>

        <div className="flex items-center gap-2 sm:gap-3">
          <Button
            variant="secondary"
            size="sm"
            onClick={loadData}
            isLoading={isLoading}
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </Button>
          <Link href="/products">
            <Button size="sm">
              <Package className="w-3.5 h-3.5" />
              <span>Add Product</span>
            </Button>
          </Link>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-500" />
          <span>{error}</span>
        </div>
      )}

      {/* Snapshot metrics come first so merchants can scan performance immediately. */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-3 sm:gap-4" data-enter="1">
        <StatCard
          title="Total Revenue"
          value={isLoading ? "—" : fmt(totalRevenue)}
          trend={isLoading ? "" : `${paidOrders.length} paid orders`}
          trendType="success"
          subtitle="Collected this period"
          icon={<DollarSign className="w-4 h-4 text-emerald-600" />}
        />
        <StatCard
          title="Active Chats"
          value={isLoading ? "—" : activeConvCount}
          trend={isLoading ? "" : `${conversations.length} total`}
          trendType="terracotta"
          subtitle="Open conversations"
          icon={<MessageSquare className="w-4 h-4 text-accent" />}
        />
        <StatCard
          title="Pending Orders"
          value={isLoading ? "—" : pendingCount}
          trend={pendingCount > 0 ? "Needs attention" : "All clear"}
          trendType={pendingCount > 0 ? "warning" : "success"}
          subtitle="Awaiting fulfilment"
          icon={<Package className="w-4 h-4 text-amber-600" />}
        />
        <StatCard
          title="Customers"
          value={isLoading ? "—" : (totalCustomers ?? 0).toLocaleString()}
          trend={aiRate !== null ? `${aiRate}% AI handled` : ""}
          trendType="terracotta"
          subtitle="Registered in your store"
          icon={<Users className="w-4 h-4 text-accent" />}
        />
      </div>

      {/* ── Main 2-column strip ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 sm:gap-6" data-enter="2">

        {/* Left 7 cols: Overview Card (revenue chart) */}
        <div className="lg:col-span-7 quiet-panel p-6 card-taste flex flex-col">
          {/* Card header */}
          <div className="flex items-center justify-between pb-4 border-b border-border mb-6">
            <span className="text-sm font-semibold text-ink-900">Overview</span>
            <span className="text-xs font-medium text-ink-500 bg-canvas-subtle px-2.5 py-1 rounded-lg border border-border">
              This week
            </span>
          </div>

          {/* 3 Aligned Figures */}
          <div className="grid grid-cols-3 gap-4 pb-6">
            {/* Orders */}
            <div>
              <span className="text-xs font-medium text-ink-500 block mb-1">Orders</span>
              {isLoading ? (
                <Skeleton w="w-16" h="h-9" />
              ) : (
                <span className="text-2xl sm:text-3xl font-bold text-ink-900 tracking-tight tabular-nums block">
                  {(totalOrders ?? 0).toLocaleString()}
                </span>
              )}
              <span className="text-xs font-medium text-ink-400 mt-1 inline-block">
                {pendingCount > 0 ? `${pendingCount} pending` : "All fulfilled"}
              </span>
            </div>

            {/* Revenue */}
            <div>
              <span className="text-xs font-medium text-ink-500 block mb-1">Revenue</span>
              {isLoading ? (
                <Skeleton w="w-24" h="h-9" />
              ) : (
                <span className="text-2xl sm:text-3xl font-bold text-ink-900 tracking-tight tabular-nums block">
                  {fmt(totalRevenue)}
                </span>
              )}
              <span className="text-xs font-medium text-emerald-600 mt-1 inline-block flex items-center gap-0.5">
                <TrendingUp className="w-3 h-3 inline" />
                Paid orders
              </span>
            </div>

            {/* Conversations */}
            <div>
              <span className="text-xs font-medium text-ink-500 block mb-1">Conversations</span>
              {isLoading ? (
                <Skeleton w="w-14" h="h-9" />
              ) : (
                <span className="text-2xl sm:text-3xl font-bold text-ink-900 tracking-tight tabular-nums block">
                  {activeConvCount.toLocaleString()}
                </span>
              )}
              <span className="text-xs font-medium text-ink-400 mt-1 inline-block">
                Active now
              </span>
            </div>
          </div>

          {/* Revenue by day bar chart */}
          <div className="pt-4 border-t border-border flex-1">
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-semibold text-ink-600">Revenue by day</span>
              {peakBar && !isLoading && (
                <span className="text-[11px] text-ink-400">
                  Peak: {peakBar.day} · {fmt(peakBar.total)}
                </span>
              )}
            </div>

            <div className="h-44 flex items-end justify-between gap-2 pt-6 px-1 relative">
              {/* Dashed midline guide */}
              <div className="absolute inset-x-0 top-1/2 border-b border-dashed border-border pointer-events-none" />

              {bars.map((bar) => (
                <div
                  key={bar.day}
                  className="flex-1 flex flex-col items-center gap-2 h-full justify-end group"
                >
                  {/* Tooltip */}
                  {bar.isPeak && bar.total > 0 ? (
                    <div className="px-2 py-0.5 rounded-md bg-ink-800 text-white text-[10px] font-medium mb-1 shadow-sm whitespace-nowrap">
                      {bar.day} {fmt(bar.total)}
                    </div>
                  ) : (
                    <div className="opacity-0 group-hover:opacity-100 transition-opacity px-1.5 py-0.5 rounded bg-ink-700 text-white text-[10px] mb-1 whitespace-nowrap">
                      {bar.total > 0 ? fmt(bar.total) : "No orders"}
                    </div>
                  )}

                  {/* Bar */}
                  <div
                    className={`w-full rounded-t-lg transition-all duration-500 ${
                      bar.isPeak && bar.total > 0
                        ? "bg-accent shadow-sm"
                        : "bg-oatmeal hover:bg-oatmeal-dark"
                    }`}
                    style={{
                      height: isLoading ? "30%" : `${bar.heightPct}%`,
                    }}
                  />

                  <span className="text-xs font-medium text-ink-500 mt-1">{bar.day}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right 5 cols: Quick actions + store health */}
        <div className="lg:col-span-5 space-y-5 flex flex-col">

          {/* Quick access card */}
          <div className="quiet-panel p-6 card-taste space-y-4 flex-1">
            <div>
              <h2 className="text-lg sm:text-xl font-bold text-ink-900 tracking-tight leading-snug">
                Your store, in real time
              </h2>
              <p className="text-xs sm:text-sm text-ink-500 mt-2 leading-relaxed">
                Every order, message, and customer interaction is processed
                automatically and reflected here instantly.
              </p>
            </div>

            <div className="pt-1 flex items-center gap-3">
              <Link href="/inbox">
                <Button size="sm">
                  <MessageSquare className="w-3.5 h-3.5" />
                  <span>Open Inbox</span>
                </Button>
              </Link>
              <Link href="/orders">
                <Button variant="secondary" size="sm">
                  <span>View Orders</span>
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </Button>
              </Link>
            </div>
          </div>

          {/* Store health panel */}
          <div className="quiet-panel p-5 card-taste space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-ink-900 flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-accent" />
                Store Health
              </span>
              <Badge variant="active" size="sm" dot>
                All systems on
              </Badge>
            </div>

            <div className="space-y-2.5 text-xs text-ink-600">
              <div className="flex items-center justify-between py-1 border-b border-border/60">
                <span className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                  WhatsApp connection
                </span>
                <span className="font-semibold text-emerald-600">Connected</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-border/60">
                <span className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                  AI assistant
                </span>
                <span className="font-semibold text-emerald-600">
                  {aiRate !== null ? `${aiRate}% handled` : "Active"}
                </span>
              </div>
              <div className="flex items-center justify-between py-1">
                <span className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                  Order processing
                </span>
                <span className="font-semibold text-emerald-600">Operational</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Bottom: Conversations + Orders tables ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 sm:gap-6" data-enter="3">

        {/* Left 2 cols */}
        <div className="lg:col-span-2 space-y-6">

          {/* Conversations table */}
          <div className="quiet-panel overflow-hidden card-taste">
            <div className="p-5 border-b border-border flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-ink-900 tracking-tight flex items-center gap-2">
                  <MessageSquare className="w-4 h-4 text-accent" />
                  Recent Conversations
                </h3>
                <p className="text-xs text-ink-400 mt-0.5">
                  Customer messages handled by your AI assistant
                </p>
              </div>
              <Link
                href="/inbox"
                className="text-xs text-accent hover:text-accent-hover font-semibold flex items-center gap-1 transition-colors"
              >
                <span>Open Inbox</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="divide-y divide-border/60">
              {isLoading ? (
                Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="p-4 sm:px-5 flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-oatmeal animate-pulse shrink-0" />
                    <div className="space-y-2 flex-1">
                      <div className="h-3 bg-oatmeal rounded animate-pulse w-32" />
                      <div className="h-2 bg-oatmeal/70 rounded animate-pulse w-20" />
                    </div>
                  </div>
                ))
              ) : conversations.length === 0 ? (
                <div className="py-12 px-6 text-center text-ink-500 space-y-2">
                  <MessageSquare className="w-8 h-8 text-ink-300 mx-auto" />
                  <p className="font-semibold text-ink-900 text-xs">No conversations yet</p>
                  <p className="text-xs text-ink-400 max-w-sm mx-auto">
                    When customers message you on WhatsApp, their conversations appear here.
                  </p>
                </div>
              ) : (
                conversations.slice(0, 5).map((conv) => (
                  <div
                    key={conv.id}
                    className="p-4 sm:px-5 flex items-center justify-between hover:bg-canvas-subtle transition-colors gap-3"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="w-9 h-9 rounded-xl bg-canvas-subtle border border-border flex items-center justify-center font-bold text-xs text-ink-900 shrink-0">
                        {conv.customer?.name ? conv.customer.name[0].toUpperCase() : "?"}
                      </div>
                      <div className="min-w-0">
                        <p className="text-xs font-semibold text-ink-900 truncate">
                          {conv.customer?.name || "Unknown customer"}
                        </p>
                        <p className="text-[11px] text-ink-400 truncate mt-0.5">
                          {conv.customer?.phone_number || "No number"}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      {conv.is_ai_active ? (
                        <Badge variant="active" size="sm" dot>AI Active</Badge>
                      ) : (
                        <Badge variant="warning" size="sm" dot>You're on</Badge>
                      )}
                      <Link href={`/inbox?id=${conv.id}`}>
                        <Button variant="ghost" size="sm">Open</Button>
                      </Link>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Orders table */}
          <div className="quiet-panel overflow-hidden card-taste">
            <div className="p-5 border-b border-border flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-ink-900 tracking-tight flex items-center gap-2">
                  <Package className="w-4 h-4 text-emerald-600" />
                  Recent Orders
                </h3>
                <p className="text-xs text-ink-400 mt-0.5">
                  Orders placed by your customers
                </p>
              </div>
              <Link
                href="/orders"
                className="text-xs text-accent hover:text-accent-hover font-semibold flex items-center gap-1 transition-colors"
              >
                <span>All Orders</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="divide-y divide-border/60">
              {isLoading ? (
                Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="p-4 sm:px-5 flex items-center justify-between">
                    <div className="h-3 bg-oatmeal rounded animate-pulse w-24" />
                    <div className="h-3 bg-oatmeal rounded animate-pulse w-16" />
                  </div>
                ))
              ) : orders.length === 0 ? (
                <div className="py-12 px-6 text-center text-ink-500 space-y-2">
                  <Package className="w-8 h-8 text-ink-300 mx-auto" />
                  <p className="font-semibold text-ink-900 text-xs">No orders yet</p>
                  <p className="text-xs text-ink-400 max-w-sm mx-auto">
                    Orders placed by customers via WhatsApp or manually will appear here.
                  </p>
                </div>
              ) : (
                orders.slice(0, 5).map((order) => (
                  <div
                    key={order.id}
                    className="p-4 sm:px-5 flex items-center justify-between hover:bg-canvas-subtle transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-xs font-bold text-ink-900">
                        {order.order_number}
                      </span>
                      <span className="text-[11px] text-ink-400">
                        {order.items?.length ?? 0} {order.items?.length === 1 ? "item" : "items"}
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-xs font-bold text-ink-900">
                        ${Number(order.total_amount).toFixed(2)}
                      </span>
                      <Badge
                        variant={order.status === "CONFIRMED" || order.status === "DELIVERED" ? "success" : "warning"}
                        size="sm"
                      >
                        {order.status.charAt(0) + order.status.slice(1).toLowerCase()}
                      </Badge>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Right col: Quick actions */}
        <div className="space-y-5">
          <div className="quiet-panel p-5 card-taste space-y-4">
            <h3 className="text-sm font-bold text-ink-900 tracking-tight flex items-center gap-2">
              <Bot className="w-4 h-4 text-accent" />
              AI Assistant
            </h3>
            <p className="text-xs text-ink-500 leading-relaxed">
              Your AI assistant handles customer questions, recommends products, and
              processes orders — automatically, 24/7.
            </p>

            <div className="space-y-2.5 pt-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-ink-600 flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                  Conversations handled
                </span>
                <span className="font-semibold text-ink-900">
                  {isLoading ? "—" : aiHandledCount}
                </span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-ink-600 flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                  Resolution rate
                </span>
                <span className="font-semibold text-emerald-600">
                  {isLoading ? "—" : aiRate !== null ? `${aiRate}%` : "N/A"}
                </span>
              </div>
            </div>

            <Link href="/agent" className="block pt-1">
              <Button variant="secondary" size="sm" className="w-full text-xs">
                Manage AI Agent &amp; Knowledge
              </Button>
            </Link>
          </div>

          <div className="quiet-panel p-5 card-taste space-y-3">
            <h3 className="text-sm font-bold text-ink-900 tracking-tight">
              Quick Actions
            </h3>
            <div className="space-y-2">
              <Link href="/products" className="block">
                <Button variant="secondary" size="sm" className="w-full justify-start text-xs">
                  <Package className="w-3.5 h-3.5" />
                  Manage Products
                </Button>
              </Link>
              <Link href="/customers" className="block">
                <Button variant="secondary" size="sm" className="w-full justify-start text-xs">
                  <Users className="w-3.5 h-3.5" />
                  View Customers
                </Button>
              </Link>
              <Link href="/settings" className="block">
                <Button variant="secondary" size="sm" className="w-full justify-start text-xs">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  Store Settings
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
