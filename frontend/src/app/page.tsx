"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  Bot,
  MessageCircle,
  PackagePlus,
  RefreshCw,
  ShoppingBag,
  UsersRound,
} from "lucide-react";
import { conversationsService } from "@/services/conversations.service";
import { customersService } from "@/services/customers.service";
import { ordersService } from "@/services/orders.service";
import type { ConversationRead, OrderRead } from "@/types";
import styles from "./page.module.css";

type Channel = "ALL" | "WHATSAPP" | "INSTAGRAM";
type Period = 7 | 30;

function localDateKey(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

interface DayTotal {
  label: string;
  value: number;
  fullDate: string;
}

interface Activity {
  id: string;
  name: string;
  detail: string;
  timestamp: string;
  kind: "order" | "chat";
  href: string;
}

function channelOf(value?: string | null): Channel | "OTHER" {
  if (value?.toUpperCase() === "WHATSAPP") return "WHATSAPP";
  if (value?.toUpperCase() === "INSTAGRAM") return "INSTAGRAM";
  return "OTHER";
}

function formatMoney(value: number, currency = "USD"): string {
  try {
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency,
      maximumFractionDigits: 0,
    }).format(value);
  } catch {
    return `${currency} ${Math.round(value).toLocaleString()}`;
  }
}

function formatRelativeDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Date unavailable";
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

function makeDayTotals(orders: OrderRead[], period: Period): DayTotal[] {
  const today = new Date();
  const totals = new Map<string, number>();
  const days = Array.from({ length: period }, (_, index) => {
    const date = new Date(today);
    date.setHours(0, 0, 0, 0);
    date.setDate(today.getDate() - (period - index - 1));
    const key = localDateKey(date);
    totals.set(key, 0);
    return {
      key,
      label: new Intl.DateTimeFormat(undefined, { weekday: period === 7 ? "short" : undefined, day: period === 30 ? "numeric" : undefined }).format(date),
      fullDate: new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" }).format(date),
    };
  });

  for (const order of orders) {
    if (order.payment_status !== "PAID") continue;
    const date = new Date(order.created_at);
    if (Number.isNaN(date.getTime())) continue;
    const key = localDateKey(date);
    if (totals.has(key)) totals.set(key, (totals.get(key) ?? 0) + Number(order.total_amount));
  }

  return days.map(({ key, label, fullDate }) => ({ label, fullDate, value: totals.get(key) ?? 0 }));
}

function getActivity(orders: OrderRead[], conversations: ConversationRead[], channel: Channel): Activity[] {
  const orderActivity: Activity[] = orders
    .filter((order) => channel === "ALL" || channelOf(order.channel) === channel)
    .map((order) => ({
      id: `order-${order.id}`,
      name: `Order ${order.order_number}`,
      detail: `${order.items.length} ${order.items.length === 1 ? "item" : "items"}, ${formatMoney(Number(order.total_amount), order.currency)}`,
      timestamp: order.created_at,
      kind: "order",
      href: "/orders",
    }));
  const chatActivity: Activity[] = conversations
    .filter((conversation) => channel === "ALL" || channelOf(conversation.channel) === channel)
    .filter((conversation) => conversation.last_message_at || conversation.created_at)
    .map((conversation) => ({
      id: `chat-${conversation.id}`,
      name: conversation.customer?.name || conversation.customer?.phone_number || "Customer conversation",
      detail: conversation.is_ai_active ? "AI assistant active" : "Team handling this chat",
      timestamp: conversation.last_message_at || conversation.created_at,
      kind: "chat",
      href: `/inbox?id=${conversation.id}`,
    }));

  return [...orderActivity, ...chatActivity]
    .sort((first, second) => new Date(second.timestamp).getTime() - new Date(first.timestamp).getTime())
    .slice(0, 6);
}

function greeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

export default function DashboardPage(): React.JSX.Element {
  const [orders, setOrders] = useState<OrderRead[]>([]);
  const [conversations, setConversations] = useState<ConversationRead[]>([]);
  const [orderCount, setOrderCount] = useState<number | null>(null);
  const [conversationCount, setConversationCount] = useState<number | null>(null);
  const [customerCount, setCustomerCount] = useState<number | null>(null);
  const [pendingCount, setPendingCount] = useState<number | null>(null);
  const [channel, setChannel] = useState<Channel>("ALL");
  const [period, setPeriod] = useState<Period>(7);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [orderResponse, conversationResponse, customerResponse, pendingResponse] = await Promise.all([
        ordersService.listOrders({ page: 1, page_size: 100 }),
        conversationsService.listConversations({ page: 1, page_size: 100 }),
        customersService.listCustomers({ page: 1, page_size: 1 }),
        ordersService.listOrders({ status: "PENDING", page: 1, page_size: 1 }),
      ]);
      setOrders(orderResponse.items);
      setOrderCount(orderResponse.total);
      setConversations(conversationResponse.items);
      setConversationCount(conversationResponse.total);
      setCustomerCount(customerResponse.total);
      setPendingCount(pendingResponse.total);
    } catch (cause: unknown) {
      setError(cause instanceof Error ? cause.message : "Could not load your store data. Try refreshing.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const visibleOrders = useMemo(
    () => orders.filter((order) => channel === "ALL" || channelOf(order.channel) === channel),
    [orders, channel],
  );
  const chartData = useMemo(() => makeDayTotals(visibleOrders, period), [visibleOrders, period]);
  const activity = useMemo(() => getActivity(orders, conversations, channel), [orders, conversations, channel]);
  const paidTotal = chartData.reduce((sum, day) => sum + day.value, 0);
  const currency = visibleOrders.find((order) => order.payment_status === "PAID")?.currency || "USD";
  const maxChartValue = Math.max(...chartData.map((day) => day.value), 1);
  const number = (value: number | null): string => (value === null ? "—" : value.toLocaleString());

  const stats = [
    { label: "Orders", value: number(orderCount), icon: ShoppingBag, note: "All time" },
    { label: "Conversations", value: number(conversationCount), icon: MessageCircle, note: "Across channels" },
    { label: "Customers", value: number(customerCount), icon: UsersRound, note: "In your store" },
    { label: "Needs fulfillment", value: number(pendingCount), icon: PackagePlus, note: "Pending orders", urgent: (pendingCount ?? 0) > 0 },
  ];

  return (
    <div className={styles.dashboard}>
      <section className={styles.welcome} aria-labelledby="dashboard-title">
        <div>
          <p className={styles.dateLine}>{new Intl.DateTimeFormat(undefined, { weekday: "long", month: "long", day: "numeric" }).format(new Date())}</p>
          <h1 id="dashboard-title">{greeting()}, welcome back.</h1>
          <p className={styles.intro}>Your conversations, orders, and customers in one place.</p>
        </div>
        <div className={styles.actions}>
          <button className={styles.refreshButton} type="button" onClick={() => void loadData()} disabled={loading} aria-label="Refresh store data">
            <RefreshCw size={16} className={loading ? styles.spinning : undefined} />
            <span>{loading ? "Refreshing" : "Refresh"}</span>
          </button>
          <Link className={styles.primaryButton} href="/products">
            <PackagePlus size={16} />
            <span>Add a product</span>
          </Link>
        </div>
      </section>

      {error && (
        <div className={styles.error} role="alert">
          <span>{error}</span>
          <button type="button" onClick={() => void loadData()}>Try again</button>
        </div>
      )}

      <section className={styles.stats} aria-label="Store totals">
        {stats.map(({ label, value, icon: Icon, note, urgent }) => (
          <div className={styles.stat} key={label}>
            <div className={styles.statHead}>
              <span>{label}</span>
              <Icon size={17} aria-hidden="true" />
            </div>
            <strong className={loading && value === "—" ? styles.loadingValue : undefined}>{value}</strong>
            <span className={urgent ? styles.urgentNote : styles.statNote}>{note}</span>
          </div>
        ))}
      </section>

      <section className={styles.overview} aria-label="Recent store activity">
        <div className={styles.chartPanel}>
          <div className={styles.panelHeader}>
            <div>
              <h2>Paid order value</h2>
              <p>Paid orders by day</p>
            </div>
            <div className={styles.periods} role="group" aria-label="Chart period">
              {([7, 30] as const).map((days) => (
                <button key={days} type="button" aria-pressed={period === days} onClick={() => setPeriod(days)}>
                  {days} days
                </button>
              ))}
            </div>
          </div>
          <div className={styles.chartSummary}>
            <strong>{formatMoney(paidTotal, currency)}</strong>
            <span>{period}-day view, latest {orders.length} orders loaded</span>
          </div>
          <div className={styles.chart} role="img" aria-label={`${period} day paid order value chart`} style={{ gridTemplateColumns: `repeat(${period}, minmax(0, 1fr))` }}>
            {chartData.map((day, index) => (
              <div className={styles.barColumn} key={`${day.fullDate}-${index}`} title={`${day.fullDate}: ${formatMoney(day.value, currency)}`}>
                <div className={styles.barTrack}>
                  <div
                    className={day.value > 0 ? styles.barFill : styles.barEmpty}
                    style={{ height: `${day.value > 0 ? Math.max(5, (day.value / maxChartValue) * 100) : 2}%` }}
                  />
                </div>
                {(period === 7 || index % 5 === 0 || index === chartData.length - 1) && <span>{day.label}</span>}
              </div>
            ))}
          </div>
          <div className={styles.chartFoot}>
            <span>Paid order value by day</span>
            <span>{period} day view</span>
          </div>
        </div>

        <div className={styles.activityPanel}>
          <div className={styles.activityHeading}>
            <div>
              <h2>Recent activity</h2>
              <p>New orders and customer chats</p>
            </div>
            <Link href="/inbox" aria-label="Open inbox"><ArrowRight size={17} /></Link>
          </div>
          <div className={styles.channelFilters} role="group" aria-label="Filter activity by channel">
            {(["ALL", "WHATSAPP", "INSTAGRAM"] as const).map((option) => (
              <button key={option} type="button" aria-pressed={channel === option} onClick={() => setChannel(option)}>
                {option === "ALL" ? "All channels" : option === "WHATSAPP" ? "WhatsApp" : "Instagram"}
              </button>
            ))}
          </div>
          {loading && activity.length === 0 ? (
            <div className={styles.activityEmpty} aria-live="polite">Loading recent activity…</div>
          ) : activity.length === 0 ? (
            <div className={styles.activityEmpty}>
              <MessageCircle size={19} />
              <strong>No activity yet</strong>
              <span>New orders and customer conversations will appear here.</span>
              <Link href="/inbox">Open the inbox <ArrowRight size={14} /></Link>
            </div>
          ) : (
            <ul className={styles.activityList}>
              {activity.map((item) => {
                const Icon = item.kind === "order" ? ShoppingBag : MessageCircle;
                return (
                  <li key={item.id}>
                    <Link href={item.href} className={styles.activityItem}>
                      <span className={item.kind === "order" ? styles.activityIcon : styles.activityIconChat}><Icon size={16} /></span>
                      <span className={styles.activityText}>
                        <strong>{item.name}</strong>
                        <span>{item.detail}</span>
                      </span>
                      <time dateTime={item.timestamp}>{formatRelativeDate(item.timestamp)}</time>
                    </Link>
                  </li>
                );
              })}
            </ul>
          )}
          <Link href="/orders" className={styles.allActivity}>View orders <ArrowRight size={15} /></Link>
        </div>
      </section>

      <section className={styles.nextSteps} aria-label="Quick actions">
        <div className={styles.nextIntro}>
          <span className={styles.nextIcon}><Bot size={19} /></span>
          <div><h2>Keep the conversation moving</h2><p>Jump into a customer chat or review orders that need attention.</p></div>
        </div>
        <div className={styles.nextLinks}>
          <Link href="/inbox">Open inbox <ArrowUpRight size={15} /></Link>
          <Link href="/orders">Review orders <ArrowDownRight size={15} /></Link>
        </div>
      </section>
    </div>
  );
}
