"use client";

/**
 * Merchant workspace header with store context, search, and account controls.
 */

import React, { useState } from "react";
import { Search, Bell, ChevronDown, Sun, Moon } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/context/ThemeContext";

export function Navbar() {
  const { user, organization } = useAuth();
  const { theme, toggleTheme }  = useTheme();
  const [searchQuery, setSearchQuery] = useState("");

  const initials = user?.full_name
    ? user.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase()
    : "A";

  return (
    <header
      style={{
        backgroundColor: "var(--g-panel)",
        borderBottom: "1px solid var(--line)",
      }}
      className="fixed top-0 right-0 z-30
                 left-[68px] sm:left-[248px]
                 h-[68px] flex items-center px-3 sm:px-6 gap-3 sm:gap-4
                 backdrop-blur-xl
                 transition-colors duration-200"
    >
      {/* ── Left: store context ─────────────────────────────────── */}
      <button
        style={{
          backgroundColor: "var(--g-subtle)",
          borderColor: "var(--line)",
          color: "var(--ink)",
        }}
        className="flex items-center gap-2 px-3 py-2 rounded-xl
                   border text-[13px] font-medium
                   hover:border-border-strong transition-colors shrink-0"
      >
        <span className="w-1.5 h-1.5 rounded-full bg-data-green shrink-0" />
        <span className="max-w-[140px] truncate">
          {organization?.name || "My Store"}
        </span>
        <ChevronDown className="w-3.5 h-3.5 shrink-0" style={{ color: "var(--ink-6)" }} />
      </button>

      {/* ── Centre: search ──────────────────────────────────────── */}
      <div className="hidden md:flex flex-1 max-w-lg relative mx-auto">
        <Search
          className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none"
          style={{ color: "var(--ink-6)" }}
        />
        <input
          type="text"
          placeholder="Search orders, products…"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{
            backgroundColor: "var(--g-subtle)",
            borderColor: "var(--line)",
            color: "var(--ink)",
          }}
          className="w-full h-10 border rounded-xl
                     pl-9 pr-14 text-[13px] placeholder:text-ink-400
                     focus:outline-none focus:ring-2 focus:ring-accent/20
                     transition-all"
          onFocus={(e) => {
            e.target.style.borderColor = "var(--action)";
            e.target.style.backgroundColor = "var(--g-panel)";
          }}
          onBlur={(e) => {
            e.target.style.borderColor = "var(--line)";
            e.target.style.backgroundColor = "var(--g-subtle)";
          }}
        />
        <kbd
          style={{
            backgroundColor: "var(--g-muted)",
            borderColor: "var(--line)",
            color: "var(--ink-5)",
          }}
          className="absolute right-2.5 top-1/2 -translate-y-1/2
                     px-1.5 py-0.5 text-[11px] font-mono border rounded-md"
        >
          ⌘K
        </kbd>
      </div>

      {/* ── Right: notifications + theme toggle + user ───────────── */}
      <div className="flex items-center gap-1.5 ml-auto">
        {/* WhatsApp connected pill */}
        <div
          style={{ borderColor: "var(--line)", color: "var(--ink-4)" }}
          className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full
                     border text-[12px] font-medium"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-data-green" />
          <span>WhatsApp</span>
        </div>

        {/* Notifications */}
        <button
          style={{ color: "var(--ink-5)" }}
          className="relative p-2 rounded-[10px]
                     hover:bg-canvas-subtle transition-colors"
          title="Notifications"
        >
          <Bell className="w-4 h-4" />
          <span className="absolute top-2 right-2 w-1.5 h-1.5 rounded-full bg-accent" />
        </button>

        {/* ── Theme toggle ──────────────────────────────────────── */}
        <button
          onClick={toggleTheme}
          title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          style={{ color: "var(--ink-5)" }}
          className="p-2 rounded-[10px] hover:bg-canvas-subtle
                     transition-all duration-200 group"
          aria-label="Toggle theme"
        >
          {theme === "dark" ? (
            <Sun
              className="w-4 h-4 group-hover:text-amber-400
                         transition-colors duration-200"
            />
          ) : (
            <Moon
              className="w-4 h-4 group-hover:text-ink-900
                         transition-colors duration-200"
            />
          )}
        </button>

        {/* User avatar */}
        <div
          style={{ borderColor: "var(--line)" }}
          className="flex items-center gap-2.5 pl-3 border-l"
        >
          <div
            style={{
              backgroundColor: "var(--action-bg)",
              borderColor: "var(--action-sub)",
            }}
            className="w-8 h-8 rounded-[10px] border
                       flex items-center justify-center text-[12px]
                       font-semibold text-accent"
          >
            {initials}
          </div>
          <div className="hidden lg:block leading-none">
            <p
              className="text-[13px] font-semibold leading-none"
              style={{ color: "var(--ink)" }}
            >
              {user?.full_name || "Store Admin"}
            </p>
            <p
              className="text-[11px] mt-0.5 leading-none"
              style={{ color: "var(--ink-5)" }}
            >
              Owner
            </p>
          </div>
        </div>
      </div>
    </header>
  );
}
