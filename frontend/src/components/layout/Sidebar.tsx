"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  MessageSquare,
  Package,
  ShoppingCart,
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
      label: "Settings",
      href: "/settings",
      icon: Settings,
      active: pathname.startsWith("/settings"),
    },
  ];

  return (
    <aside className="fixed left-0 top-0 bottom-0 w-16 sm:w-60 bg-obsidian-900 border-r border-obsidian-750 flex flex-col justify-between z-40">
      <div>
        {/* Brand Logo Header */}
        <div className="h-16 flex items-center px-3 sm:px-5 border-b border-obsidian-750/70 gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-emerald to-brand-whatsapp flex items-center justify-center text-obsidian-950 font-bold font-mono text-lg shadow-glow">
            C.
          </div>
          <div className="hidden sm:block overflow-hidden">
            <h1 className="text-sm font-bold text-white tracking-tight flex items-center gap-1.5">
              Chatrio <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-brand-emerald/10 text-brand-emerald border border-brand-emerald/20">AI</span>
            </h1>
            <p className="text-[11px] text-obsidian-400 truncate">
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
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all group relative",
                  item.active
                    ? "bg-obsidian-800 text-white border border-obsidian-650 shadow-sm"
                    : "text-obsidian-400 hover:text-white hover:bg-obsidian-850"
                )}
                title={item.label}
              >
                <Icon
                  className={clsx(
                    "w-4 h-4 shrink-0 transition-colors",
                    item.active ? "text-brand-emerald" : "text-obsidian-400 group-hover:text-white"
                  )}
                />
                <span className="hidden sm:inline-block flex-1 truncate">{item.label}</span>
                {item.badge && (
                  <span className="hidden sm:inline-flex items-center text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-brand-emerald/20 text-brand-emerald border border-brand-emerald/30 animate-pulse">
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Footer / Account / Sign Out */}
      <div className="p-2 sm:p-3 border-t border-obsidian-750/70 space-y-2">
        <div className="hidden sm:flex items-center gap-2 px-3 py-2 rounded-lg bg-obsidian-850/60 border border-obsidian-750 text-xs text-obsidian-300">
          <Bot className="w-3.5 h-3.5 text-brand-cyan" />
          <span className="truncate">AI Agent: Active</span>
        </div>
        <button
          onClick={logout}
          className="w-full flex items-center justify-center sm:justify-start gap-3 px-3 py-2 rounded-lg text-xs font-medium text-obsidian-400 hover:text-brand-rose hover:bg-brand-rose/10 transition-colors"
          title="Sign out"
        >
          <LogOut className="w-4 h-4 shrink-0" />
          <span className="hidden sm:inline">Sign Out</span>
        </button>
      </div>
    </aside>
  );
}

