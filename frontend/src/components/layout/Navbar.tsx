"use client";

import React, { useState } from "react";
import { Search, Bell, Sparkles, ChevronDown } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

export function Navbar() {
  const { user, organization } = useAuth();
  const [searchQuery, setSearchQuery] = useState("");

  return (
    <header className="h-16 bg-obsidian-900/80 backdrop-blur border-b border-obsidian-750/70 fixed top-0 right-0 left-16 sm:left-60 z-30 px-4 sm:px-6 flex items-center justify-between">
      {/* Left: Organization context selector */}
      <div className="flex items-center gap-2 sm:gap-3">
        <button className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-obsidian-800 border border-obsidian-700 text-xs font-semibold text-white hover:border-obsidian-600 transition-colors">
          <span className="w-2 h-2 rounded-full bg-brand-emerald animate-pulse" />
          <span className="max-w-[120px] sm:max-w-[180px] truncate">
            {organization?.name || "Main Store"}
          </span>
          <ChevronDown className="w-3.5 h-3.5 text-obsidian-400" />
        </button>
      </div>

      {/* Center: Global Search Bar with keyboard shortcut */}
      <div className="hidden md:flex items-center w-full max-w-md mx-4">
        <div className="relative w-full">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-obsidian-400 pointer-events-none" />
          <input
            type="text"
            placeholder="Search orders, products, conversations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-obsidian-850 border border-obsidian-700/80 rounded-lg pl-9 pr-14 py-1.5 text-xs text-obsidian-200 placeholder:text-obsidian-500 focus:outline-none focus:border-brand-emerald focus:ring-1 focus:ring-brand-emerald"
          />
          <kbd className="absolute right-2.5 top-1/2 -translate-y-1/2 px-1.5 py-0.5 text-[10px] font-mono font-medium text-obsidian-400 bg-obsidian-800 border border-obsidian-700 rounded">
            ⌘K
          </kbd>
        </div>
      </div>

      {/* Right: Notifications, Live Signal, Profile */}
      <div className="flex items-center gap-2 sm:gap-3">
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-brand-emerald/10 border border-brand-emerald/20 text-[11px] font-medium text-brand-emerald">
          <Sparkles className="w-3 h-3" />
          <span>Meta Cloud: Connected</span>
        </div>

        <button
          className="p-2 rounded-lg text-obsidian-400 hover:text-white hover:bg-obsidian-800 transition-colors relative"
          title="Notifications"
        >
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-brand-emerald" />
        </button>

        {/* Profile Avatar Pill */}
        <div className="flex items-center gap-2 pl-2 border-l border-obsidian-750">
          <div className="w-7 h-7 rounded-lg bg-obsidian-800 border border-obsidian-700 flex items-center justify-center text-xs font-bold text-white font-mono">
            {user?.first_name ? user.first_name[0].toUpperCase() : "A"}
          </div>
          <div className="hidden lg:block text-left">
            <p className="text-xs font-semibold text-white leading-none">
              {user?.first_name} {user?.last_name}
            </p>
            <p className="text-[10px] text-obsidian-400 leading-none mt-1">
              Store Owner
            </p>
          </div>
        </div>
      </div>
    </header>
  );
}

