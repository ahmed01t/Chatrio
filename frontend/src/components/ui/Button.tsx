"use client";

/**
 * Button — Chatrio interface button, light and dark theme aware
 *
 * - primary: filled brand indigo for the primary action
 * - secondary: quiet white/panel border button
 * - ghost: text-only
 * - danger: soft rose
 * - Step on hover (brightness 95%), press on click (scale 0.97)
 * - 10px border-radius (soft scale)
 */

import React from "react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger" | "ghost" | "outline";
  size?: "sm" | "md" | "lg";
  isLoading?: boolean;
}

export function Button({
  className,
  variant = "primary",
  size = "md",
  isLoading = false,
  children,
  disabled,
  ...props
}: ButtonProps) {
  const base =
    "inline-flex items-center justify-center gap-2 font-medium select-none whitespace-nowrap " +
    "transition-all duration-150 cursor-pointer " +
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 " +
    "focus-visible:ring-accent " +
    "disabled:opacity-40 disabled:cursor-not-allowed " +
    "hover:brightness-95 active:scale-[0.97] active:brightness-90";

  const radius = "rounded-[10px]";

  const sizes = {
    sm: "h-9  px-3.5 text-[13px]",
    md: "h-10 px-4   text-[14px]",
    lg: "h-11 px-5   text-[15px]",
  };

  /* Inline style objects for variants that need CSS vars */
  const variantClass = {
    primary: "bg-accent text-white hover:bg-accent-hover shadow-sm font-semibold",
    secondary: "font-medium",
    danger:   "font-medium",
    ghost:    "font-medium",
    outline:  "font-medium",
  };

  /* Extra inline styles for dark-mode-aware variants */
  const variantStyle: Record<string, React.CSSProperties> = {
    primary:   {},
    secondary: {
      backgroundColor: "var(--g-panel)",
      color:           "var(--ink-2)",
      border:          "1px solid var(--line)",
    },
    danger: {
      backgroundColor: "rgba(220, 38, 38, 0.08)",
      color:           "#F87171",
      border:          "1px solid rgba(220, 38, 38, 0.25)",
    },
    ghost: {
      backgroundColor: "transparent",
      color:           "var(--ink-4)",
    },
    outline: {
      backgroundColor: "transparent",
      color:           "var(--ink-3)",
      border:          "1px solid var(--line)",
    },
  };

  return (
    <button
      className={twMerge(
        clsx(base, radius, sizes[size], variantClass[variant], className)
      )}
      style={variantStyle[variant]}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <>
          <svg
            className="animate-spin w-3.5 h-3.5 text-current"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12" cy="12" r="10"
              stroke="currentColor" strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8v8H4z"
            />
          </svg>
          <span>Loading…</span>
        </>
      ) : (
        children
      )}
    </button>
  );
}
