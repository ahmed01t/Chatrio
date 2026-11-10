"use client";

/**
 * Navbar — tasteskill.dev inspired
 *
 * - Fixed, full-width, 68px tall, 1px hairline bottom border
 * - Opaque white — no blur, no colour flip, no transparency
 * - Store context pill left, search centre, user right
 */

import React, { useState } from "react";
import { Search, Bell, ChevronDown } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

export function Navbar() {
  const { user, organization } = useAuth();
  const [searchQuery, setSearchQuery] = useState("");

  const initials = user?.full_name
    ? user.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase()
    : "A";

  return (
    <header
      className="fixed top-0 right-0 z-30
                 left-[60px] sm:left-[232px]
                 h-[68px] bg-white border-b border-border
                 flex items-center px-4 sm:px-6 gap-4"
    >
      {/* ── Left: store context ─────────────────────────────────── */}
      <button
        className="flex items-center gap-2 px-3 py-1.5 rounded-[10px]
                   bg-canvas-subtle border border-border text-[13px] font-medium
                   text-ink-800 hover:border-border-strong transition-colors shrink-0"
      >
        <span className="w-1.5 h-1.5 rounded-full bg-data-green shrink-0" />
        <span className="max-w-[140px] truncate">
          {organization?.name || "My Store"}
        </span>
        <ChevronDown className="w-3.5 h-3.5 text-ink-400 shrink-0" />
      </button>

      {/* ── Centre: search ──────────────────────────────────────── */}
      <div className="hidden md:flex flex-1 max-w-sm relative mx-auto">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-400 pointer-events-none" />
        <input
          type="text"
          placeholder="Search orders, products…"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full h-9 bg-canvas-subtle border border-border rounded-[10px]
                     pl-9 pr-14 text-[13px] text-ink-900 placeholder:text-ink-400
                     focus:outline-none focus:border-accent focus:bg-white
                     focus:ring-2 focus:ring-accent/20 transition-all"
        />
        <kbd
          className="absolute right-2.5 top-1/2 -translate-y-1/2
                     px-1.5 py-0.5 text-[11px] font-mono text-ink-400
                     bg-white border border-border rounded-md"
        >
          ⌘K
        </kbd>
      </div>

      {/* ── Right: notifications + user ─────────────────────────── */}
      <div className="flex items-center gap-2 ml-auto">
        {/* WhatsApp connected pill */}
        <div
          className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full
                     border border-border text-[12px] font-medium text-ink-600"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-data-green" />
          <span>WhatsApp</span>
        </div>

        {/* Notifications */}
        <button
          className="relative p-2 rounded-[10px] text-ink-500
                     hover:text-ink-900 hover:bg-canvas-subtle transition-colors"
          title="Notifications"
        >
          <Bell className="w-4 h-4" />
          <span
            className="absolute top-2 right-2 w-1.5 h-1.5
                       rounded-full bg-accent"
          />
        </button>

        {/* User avatar */}
        <div className="flex items-center gap-2.5 pl-3 border-l border-border">
          <div
            className="w-8 h-8 rounded-[10px] bg-accent/10 border border-accent/20
                       flex items-center justify-center text-[12px] font-semibold
                       text-accent"
          >
            {initials}
          </div>
          <div className="hidden lg:block leading-none">
            <p className="text-[13px] font-semibold text-ink-900">
              {user?.full_name || "Store Admin"}
            </p>
            <p className="text-[11px] text-ink-500 mt-0.5">Owner</p>
          </div>
        </div>
      </div>
    </header>
  );
}
