"use client";

import React from "react";
import { usePathname } from "next/navigation";
import { Sidebar } from "./Sidebar";
import { Navbar } from "./Navbar";
import { useAuth } from "@/context/AuthContext";
import { Theme } from "@astryxdesign/core/theme";
import { defaultThemeSlug, themes } from "@/astryx-themes";
import { useTheme } from "@/context/ThemeContext";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname  = usePathname();
  const { isLoading } = useAuth();
  const { theme } = useTheme();
  const isAuthPage =
    pathname.startsWith("/login") || pathname.startsWith("/register");

  let content: React.ReactNode;
  if (isAuthPage) {
    content = (
      <main className="min-h-screen canvas-glow" style={{ color: "var(--ink)" }}>
        {children}
      </main>
    );
  } else if (isLoading) {
    content = (
      <div
        className="min-h-screen flex items-center justify-center"
        style={{ backgroundColor: "var(--g-main)" }}
      >
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 rounded-[10px] bg-accent flex items-center justify-center text-white font-semibold text-lg animate-pulse">
            C
          </div>
          <p className="text-[13px]" style={{ color: "var(--ink-5)" }}>
            Loading…
          </p>
        </div>
      </div>
    );
  } else {
    content = (
      <div
        className="min-h-screen flex transition-colors duration-200"
        style={{ backgroundColor: "var(--g-main)", color: "var(--ink)" }}
      >
        <Sidebar />
        <div className="flex-1 pl-[68px] sm:pl-[248px] flex flex-col min-h-screen">
          <Navbar />
          <main className="flex-1 mt-[68px] p-4 sm:p-6 lg:p-8">
            <div className="max-w-[1440px] mx-auto w-full page-enter">
              {children}
            </div>
          </main>
        </div>
      </div>
    );
  }

  return (
    <Theme theme={themes[defaultThemeSlug]} mode={theme}>
      {content}
    </Theme>
  );
}
