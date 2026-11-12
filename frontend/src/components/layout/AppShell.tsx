"use client";

import React, { useEffect, useState } from "react";
import type { JSX } from "react";
import { usePathname } from "next/navigation";
import { Sidebar } from "./Sidebar";
import { Navbar } from "./Navbar";
import { useAuth } from "@/context/AuthContext";
import { BrandMark } from "@/components/brand/BrandMark";
import { WelcomeTransition } from "@/components/auth/WelcomeTransition";

export function AppShell({ children }: { children: React.ReactNode }): JSX.Element {
  const pathname  = usePathname();
  const { isLoading, isAuthenticated, organization, welcomePending, consumeWelcomeTransition } = useAuth();
  const [showWelcome, setShowWelcome] = useState(false);
  const isAuthPage =
    pathname.startsWith("/login") || pathname.startsWith("/register");

  useEffect(() => {
    if (pathname !== "/") {
      setShowWelcome(false);
      if (welcomePending) consumeWelcomeTransition();
      return;
    }
    if (isLoading || !isAuthenticated || !welcomePending) return;

    setShowWelcome(true);
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const timeout = window.setTimeout(() => {
      setShowWelcome(false);
      consumeWelcomeTransition();
    }, reducedMotion ? 220 : 1480);
    return () => window.clearTimeout(timeout);
  }, [pathname, isAuthenticated, isLoading, welcomePending, consumeWelcomeTransition]);

  let content: React.ReactNode;
  if (isAuthPage) {
    content = (
      <div className="min-h-screen" style={{ color: "var(--ink)" }}>
        {children}
      </div>
    );
  } else if (isLoading) {
    content = (
      <div
        className="min-h-screen flex items-center justify-center"
        style={{ backgroundColor: "var(--g-main)" }}
      >
        <div className="flex flex-col items-center gap-4">
          <BrandMark size="medium" />
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
    <>
      <div inert={showWelcome || undefined} aria-hidden={showWelcome || undefined}>{content}</div>
      {showWelcome && <WelcomeTransition organizationName={organization?.name || "your store"} />}
    </>
  );
}
