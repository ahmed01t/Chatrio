"use client";

/**
 * Sidebar — tasteskill.dev inspired
 *
 * - White quiet-panel left rail, 1px hairline right border
 * - Active item: terracotta pill on left edge + accent tint bg
 * - Hover: ink-900 text + subtle bg (no colour)
 * - 60px collapsed / 232px expanded
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
  Activity,
  Settings,
  LogOut,
} from "lucide-react";
import { clsx } from "clsx";
import { useAuth } from "@/context/AuthContext";

const navItems = [
  { label: "Overview",   href: "/",           icon: LayoutDashboard, exact: true  },
  { label: "Inbox",      href: "/inbox",       icon: MessageSquare,   badge: "LIVE" },
  { label: "Products",   href: "/products",    icon: Package  },
  { label: "Orders",     href: "/orders",      icon: ShoppingCart },
  { label: "Customers",  href: "/customers",   icon: Users    },
  { label: "Analytics",  href: "/analytics",   icon: Activity },
  { label: "Settings",   href: "/settings",    icon: Settings },
];

export function Sidebar() {
  const pathname  = usePathname();
  const { logout, organization } = useAuth();

  function isActive(item: (typeof navItems)[0]) {
    if (item.exact) return pathname === item.href;
    return pathname.startsWith(item.href);
  }

  return (
    <aside
      className="fixed inset-y-0 left-0 z-40 flex flex-col
                 w-[60px] sm:w-[232px]
                 bg-white border-r border-border"
    >
      {/* ── Brand ──────────────────────────────────────────────── */}
      <div
        className="h-[68px] flex items-center px-3 sm:px-4
                   border-b border-border gap-3 shrink-0"
      >
        {/* Logo mark */}
        <div
          className="w-9 h-9 rounded-[10px] bg-accent flex items-center
                     justify-center font-semibold text-white text-base shrink-0"
        >
          C
        </div>

        <div className="hidden sm:block min-w-0">
          <span className="block text-[15px] font-semibold text-ink-900 leading-none tracking-tight">
            Chatrio
          </span>
          <span className="block text-[12px] text-ink-500 mt-0.5 truncate leading-none">
            {organization?.name || "My Store"}
          </span>
        </div>
      </div>

      {/* ── Nav ──────────────────────────────────────────────────── */}
      <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-0.5">
        {navItems.map((item) => {
          const Icon   = item.icon;
          const active = isActive(item);

          return (
            <Link
              key={item.href}
              href={item.href}
              title={item.label}
              className={clsx(
                "relative flex items-center gap-3 px-3 py-2.5 rounded-[10px]",
                "text-[14px] font-medium transition-all duration-150",
                active
                  ? "bg-accent-light text-accent"
                  : "text-ink-600 hover:text-ink-900 hover:bg-canvas-subtle"
              )}
            >
              {/* Active left pill */}
              {active && (
                <span
                  className="absolute left-0 top-1/2 -translate-y-1/2
                             w-[3px] h-5 rounded-r-full bg-accent"
                />
              )}

              <Icon
                className={clsx(
                  "w-[18px] h-[18px] shrink-0 transition-colors",
                  active ? "text-accent" : "text-ink-400"
                )}
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
      <div className="shrink-0 px-2 pb-4 border-t border-border pt-3">
        <button
          onClick={logout}
          title="Sign out"
          className="w-full flex items-center justify-center sm:justify-start
                     gap-3 px-3 py-2.5 rounded-[10px]
                     text-[13px] font-medium text-ink-500
                     hover:text-rose-600 hover:bg-rose-50 transition-colors"
        >
          <LogOut className="w-[18px] h-[18px] shrink-0" />
          <span className="hidden sm:inline">Sign out</span>
        </button>
      </div>
    </aside>
  );
}
