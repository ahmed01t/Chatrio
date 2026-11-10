"use client";

import React from "react";
import { usePathname } from "next/navigation";
import { Sidebar } from "./Sidebar";
import { Navbar } from "./Navbar";
import { useAuth } from "@/context/AuthContext";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname  = usePathname();
  const { isLoading } = useAuth();
  const isAuthPage =
    pathname.startsWith("/login") || pathname.startsWith("/register");

  /* Auth pages — full-screen canvas with warm ambient glow */
  if (isAuthPage) {
    return (
      <main className="min-h-screen canvas-glow text-ink-900">
        {children}
      </main>
    );
  }

  /* Loading splash */
  if (isLoading) {
    return (
      <div className="min-h-screen bg-canvas flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div
            className="w-10 h-10 rounded-[10px] bg-accent flex items-center
                       justify-center text-white font-semibold text-lg
                       animate-pulse"
          >
            C
          </div>
          <p className="text-[13px] text-ink-500">Loading…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-canvas text-ink-900 flex">
      <Sidebar />

      {/* Main area offset by sidebar width */}
      <div className="flex-1 pl-[60px] sm:pl-[232px] flex flex-col min-h-screen">
        <Navbar />

        {/* Page content — 68px top offset for fixed navbar */}
        <main className="flex-1 mt-[68px] p-4 sm:p-6 lg:p-8">
          <div className="max-w-[1280px] mx-auto w-full">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
