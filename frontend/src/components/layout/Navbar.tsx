"use client";

import { Moon, Sun } from "lucide-react";
import { usePathname } from "next/navigation";
import type { JSX } from "react";
import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/context/ThemeContext";

const routeTitles: Array<{ href: string; title: string }> = [
  { href: "/inbox", title: "Inbox" },
  { href: "/products", title: "Products" },
  { href: "/orders", title: "Orders" },
  { href: "/customers", title: "Customers" },
  { href: "/agent", title: "AI agent" },
  { href: "/organization", title: "Organization" },
  { href: "/settings", title: "Settings" },
];

export function Navbar(): JSX.Element {
  const pathname = usePathname();
  const { user, organization } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const title = pathname === "/"
    ? "Overview"
    : routeTitles.find((route) => pathname.startsWith(route.href))?.title || "Workspace";
  const initials = user?.full_name
    ? user.full_name.split(" ").map((part) => part[0]).join("").slice(0, 2).toUpperCase()
    : "A";

  return (
    <header
      style={{ backgroundColor: "var(--g-panel)", borderBottom: "1px solid var(--line)" }}
      className="fixed top-0 right-0 z-30 left-[68px] sm:left-[248px] h-[68px] flex items-center justify-between px-4 sm:px-6 transition-colors duration-200"
    >
      <div className="min-w-0">
        <p className="truncate text-xs" style={{ color: "var(--ink-5)" }}>
          {organization?.name || "My Store"}
        </p>
        <h2 className="truncate text-sm font-semibold leading-tight" style={{ color: "var(--ink)" }}>
          {title}
        </h2>
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={toggleTheme}
          title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          style={{ color: "var(--ink-5)" }}
          className="grid min-h-11 min-w-11 place-items-center rounded-xl transition-colors hover:bg-accent-light hover:text-accent focus-visible:ring-2 focus-visible:ring-accent"
          aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          type="button"
        >
          {theme === "dark" ? <Sun size={17} /> : <Moon size={17} />}
        </button>

        <div className="flex items-center gap-2.5 border-l pl-3" style={{ borderColor: "var(--line)" }}>
          <span
            className="grid h-9 w-9 place-items-center rounded-xl border text-xs font-semibold"
            style={{ backgroundColor: "var(--action-bg)", borderColor: "var(--action-sub)", color: "var(--action)" }}
            aria-label={`Signed in as ${user?.full_name || "Store Admin"}`}
          >
            {initials}
          </span>
          <span className="hidden max-w-40 sm:block">
            <span className="block truncate text-xs font-semibold" style={{ color: "var(--ink)" }}>
              {user?.full_name || "Store Admin"}
            </span>
            <span className="block text-xs" style={{ color: "var(--ink-5)" }}>Merchant workspace</span>
          </span>
        </div>
      </div>
    </header>
  );
}
