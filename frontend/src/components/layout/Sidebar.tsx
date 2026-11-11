"use client";

/**
 * Sidebar — tasteskill.dev inspired, dark-mode aware
 * Uses CSS custom properties directly so tokens swap automatically on html.dark
 */

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  MessageSquare,
  Package,
  ShoppingCart,
  Users,
  Bot,
  Building2,
  Settings,
  LogOut,
} from "lucide-react";
import { clsx } from "clsx";
import { useAuth } from "@/context/AuthContext";

const navItems = [
  { label: "Overview",     href: "/",             icon: LayoutDashboard, exact: true },
  { label: "Inbox",        href: "/inbox",        icon: MessageSquare,   badge: "LIVE" },
  { label: "Products",     href: "/products",     icon: Package   },
  { label: "Orders",       href: "/orders",       icon: ShoppingCart },
  { label: "Customers",    href: "/customers",    icon: Users     },
  { label: "AI Agent",     href: "/agent",        icon: Bot       },
  { label: "Organization", href: "/organization", icon: Building2 },
  { label: "Settings",     href: "/settings",     icon: Settings  },
];

export function Sidebar() {
  const pathname              = usePathname();
  const { logout, organization } = useAuth();

  function isActive(item: (typeof navItems)[0]) {
    return item.exact ? pathname === item.href : pathname.startsWith(item.href);
  }

  return (
    <aside
      style={{
        backgroundColor: "var(--g-panel)",
        borderRight: "1px solid var(--line)",
      }}
      aria-label="Main navigation"
      className="fixed inset-y-0 left-0 z-40 flex flex-col
                 w-[68px] sm:w-[248px] transition-colors duration-200"
    >
      {/* ── Brand ──────────────────────────────────────────────── */}
      <div
        style={{ borderBottom: "1px solid var(--line)" }}
        className="h-[68px] flex items-center px-3 sm:px-5 gap-3 shrink-0"
      >
        <div
          className="w-10 h-10 rounded-[13px] bg-gradient-to-br from-indigo-500 to-violet-700 flex items-center
                     justify-center font-bold text-white text-base shrink-0 shadow-lg shadow-indigo-950/20 ring-1 ring-white/25"
        >
          C
        </div>
        <div className="hidden sm:block min-w-0">
          <span
            style={{ color: "var(--ink)" }}
            className="block text-[15px] font-semibold leading-none tracking-tight"
          >
            Chatrio
          </span>
          <span
            style={{ color: "var(--ink-5)" }}
            className="block text-[12px] mt-0.5 truncate leading-none"
          >
            {organization?.name || "My Store"}
          </span>
        </div>
      </div>

      {/* ── Nav ──────────────────────────────────────────────────── */}
      <nav className="flex-1 overflow-y-auto py-5 px-2.5 sm:px-3 space-y-1">
        <p className="hidden sm:block px-3 pb-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-ink-400">
          Workspace
        </p>
        {navItems.map((item) => {
          const Icon   = item.icon;
          const active = isActive(item);

          return (
            <Link
              key={item.href}
              href={item.href}
              title={item.label}
              aria-current={active ? "page" : undefined}
              style={
                active
                  ? {
                      backgroundColor: "var(--action-bg)",
                      color: "var(--action)",
                    }
                  : { color: "var(--ink-4)" }
              }
              className={clsx(
                "relative flex items-center gap-3 px-3 py-2.5 rounded-xl",
                "text-[13px] font-medium transition-all duration-200",
                !active && "hover:bg-canvas-subtle"
              )}
            >
              {/* Active left pill */}
              {active && (
                <span
                  className="absolute left-0 top-1/2 -translate-y-1/2
                             w-[3px] h-5 rounded-r-full bg-accent ring-1 ring-violet-300/30"
                />
              )}

              <Icon
                className={clsx(
                  "w-[18px] h-[18px] shrink-0 transition-colors",
                  active ? "text-accent" : ""
                )}
                style={active ? {} : { color: "var(--ink-6)" }}
              />

              <span className="hidden sm:block flex-1 truncate">
                {item.label}
              </span>

              {item.badge && (
                <span
                  className="hidden sm:inline-flex text-[10px] font-bold
                             px-1.5 py-0.5 rounded-full bg-accent text-white"
                >
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* ── Footer ───────────────────────────────────────────────── */}
      <div
        style={{ borderTop: "1px solid var(--line)" }}
        className="shrink-0 px-2.5 sm:px-3 pb-4 pt-3"
      >
        <button
          onClick={logout}
          title="Sign out"
          style={{ color: "var(--ink-5)" }}
          className="w-full flex items-center justify-center sm:justify-start
                     gap-3 px-3 py-2.5 rounded-[10px]
                     text-[13px] font-medium transition-colors
                     hover:text-rose-500 hover:bg-rose-500/10"
        >
          <LogOut className="w-[18px] h-[18px] shrink-0" />
          <span className="hidden sm:inline">Sign out</span>
        </button>
      </div>
    </aside>
  );
}
