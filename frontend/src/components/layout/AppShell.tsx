"use client";

import React from "react";
import { usePathname } from "next/navigation";
import { Sidebar } from "./Sidebar";
import { Navbar } from "./Navbar";
import { useAuth } from "@/context/AuthContext";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { isLoading } = useAuth();
  const isAuthPage = pathname.startsWith("/login") || pathname.startsWith("/register");

  if (isAuthPage) {
    return <main className="min-h-screen bg-obsidian-950 text-white">{children}</main>;
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-obsidian-950 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-emerald to-brand-whatsapp flex items-center justify-center font-bold text-obsidian-950 font-mono text-xl animate-pulse">
            C.
          </div>
          <p className="text-xs text-obsidian-400 font-mono">Loading Chatrio Engine...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-obsidian-950 text-obsidian-100 flex">
      <Sidebar />
      <div className="flex-1 pl-16 sm:pl-60 flex flex-col min-h-screen">
        <Navbar />
        <main className="flex-1 mt-16 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
}

