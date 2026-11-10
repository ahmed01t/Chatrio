"use client";

import React, { useState } from "react";
import { Search, Bell, Sparkles, ChevronDown } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

export function Navbar() {
  const { user, organization } = useAuth();
  const [searchQuery, setSearchQuery] = useState("");

  return (
    <header className="h-16 bg-white/80 backdrop-blur border-b border-border fixed top-0 right-0 left-16 sm:left-60 z-30 px-4 sm:px-6 flex items-center justify-between">
      {/* Left: Organization context selector */}
      <div className="flex items-center gap-2 sm:gap-3">
        <button className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-canvas-subtle border border-border text-xs font-semibold text-ink-900 hover:border-border-strong transition-colors">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="max-w-[120px] sm:max-w-[180px] truncate">
            {organization?.name || "Main Store"}
          </span>
          <ChevronDown className="w-3.5 h-3.5 text-ink-400" />
        </button>
      </div>

      {/* Center: Global Search Bar with keyboard shortcut */}
      <div className="hidden md:flex items-center w-full max-w-md mx-4">
        <div className="relative w-full">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-ink-400 pointer-events-none" />
          <input
            type="text"
            placeholder="Search orders, products, conversations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-canvas-subtle border border-border rounded-xl pl-9 pr-14 py-1.5 text-xs text-ink-900 placeholder:text-ink-400 focus:outline-none focus:border-accent focus:bg-white focus:ring-1 focus:ring-accent transition-all"
          />
          <kbd className="absolute right-2.5 top-1/2 -translate-y-1/2 px-1.5 py-0.5 text-[10px] font-mono font-medium text-ink-500 bg-white border border-border rounded-md shadow-sm">
            ⌘K
          </kbd>
        </div>
      </div>

      {/* Right: Notifications, Live Signal, Profile */}
      <div className="flex items-center gap-2 sm:gap-3">
        <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-[11px] font-semibold text-emerald-700">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span>Meta Cloud API: Live</span>
        </div>

        <button
          className="p-2 rounded-xl text-ink-500 hover:text-ink-900 hover:bg-canvas-subtle transition-colors relative"
          title="Notifications"
        >
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-accent" />
        </button>

        {/* Profile Avatar Pill */}
        <div className="flex items-center gap-2.5 pl-2 border-l border-border">
          <div className="w-8 h-8 rounded-xl bg-canvas-subtle border border-border flex items-center justify-center text-xs font-bold text-ink-900 font-mono">
            {user?.full_name ? user.full_name[0].toUpperCase() : "A"}
          </div>
          <div className="hidden lg:block text-left">
            <p className="text-xs font-bold text-ink-900 leading-none">
              {user?.full_name || "Store Admin"}
            </p>
            <p className="text-[10px] text-ink-500 leading-none mt-1">
              Store Owner
            </p>
          </div>
        </div>
      </div>
    </header>
  );
}
