"use client";

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
  Bot,
  LogOut,
} from "lucide-react";
import { clsx } from "clsx";
import { useAuth } from "@/context/AuthContext";

export function Sidebar() {
  const pathname = usePathname();
  const { logout, organization } = useAuth();

  const navItems = [
    {
      label: "Overview",
      href: "/",
      icon: LayoutDashboard,
      active: pathname === "/",
    },
    {
      label: "Live Inbox",
      href: "/inbox",
      icon: MessageSquare,
      active: pathname.startsWith("/inbox"),
      badge: "LIVE",
    },
    {
      label: "Products",
      href: "/products",
      icon: Package,
      active: pathname.startsWith("/products"),
    },
    {
      label: "Orders",
      href: "/orders",
      icon: ShoppingCart,
      active: pathname.startsWith("/orders"),
    },
    {
      label: "Customers",
      href: "/customers",
      icon: Users,
      active: pathname.startsWith("/customers"),
    },
    {
      label: "Analytics",
      href: "/analytics",
      icon: Activity,
      active: pathname.startsWith("/analytics"),
    },
    {
      label: "Settings",
      href: "/settings",
      icon: Settings,
      active: pathname.startsWith("/settings"),
    },
  ];

  return (
    <aside className="fixed left-0 top-0 bottom-0 w-16 sm:w-60 bg-white border-r border-border flex flex-col justify-between z-40">
      <div>
        {/* Brand Logo Header */}
        <div className="h-16 flex items-center px-3 sm:px-5 border-b border-border gap-3">
          <div className="w-9 h-9 rounded-xl bg-accent text-white flex items-center justify-center font-bold font-mono text-lg shadow-sm">
            C.
          </div>
          <div className="hidden sm:block overflow-hidden">
            <h1 className="text-sm font-bold text-ink-900 tracking-tight flex items-center gap-1.5">
              Chatrio <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-accent-light text-accent border border-accent-subtle font-semibold">AI</span>
            </h1>
            <p className="text-[11px] text-ink-500 truncate">
              {organization?.name || "WhatsApp Commerce"}
            </p>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="p-2 sm:p-3 space-y-1 mt-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={clsx(
                  "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all group relative",
                  item.active
                    ? "bg-accent-light text-accent border border-accent-subtle font-semibold shadow-sm"
                    : "text-ink-600 hover:text-ink-900 hover:bg-canvas-subtle"
                )}
                title={item.label}
              >
                <Icon
                  className={clsx(
                    "w-4 h-4 shrink-0 transition-colors",
                    item.active ? "text-accent" : "text-ink-400 group-hover:text-ink-900"
                  )}
                />
                <span className="hidden sm:inline-block flex-1 truncate">{item.label}</span>
                {item.badge && (
                  <span className="hidden sm:inline-flex items-center text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-accent text-white">
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Footer / Account / Sign Out */}
      <div className="p-2 sm:p-3 border-t border-border space-y-2">
        <div className="hidden sm:flex items-center gap-2 px-3 py-2 rounded-xl bg-canvas-subtle border border-border text-xs text-ink-600">
          <Bot className="w-3.5 h-3.5 text-accent" />
          <span className="truncate font-medium">LangGraph: Active</span>
        </div>
        <button
          onClick={logout}
          className="w-full flex items-center justify-center sm:justify-start gap-3 px-3 py-2 rounded-xl text-xs font-semibold text-ink-500 hover:text-rose-600 hover:bg-rose-50 transition-colors"
          title="Sign out"
        >
          <LogOut className="w-4 h-4 shrink-0" />
          <span className="hidden sm:inline">Sign Out</span>
        </button>
      </div>
    </aside>
  );
}
