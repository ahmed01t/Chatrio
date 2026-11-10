"use client";

/**
 * Button — tasteskill.dev design system
 *
 * Rules:
 * - Exactly one filled button = main action (primary)
 * - Secondary: white/quiet, border hairline
 * - Buttons step on hover (brightness), press on click (scale 0.97)
 * - 44px minimum height, 10px border-radius (soft scale)
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
    "inline-flex items-center justify-center gap-2 font-medium select-none " +
    "transition-all duration-150 cursor-pointer " +
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 " +
    "focus-visible:ring-accent focus-visible:ring-offset-canvas " +
    "disabled:opacity-40 disabled:cursor-not-allowed " +
    // step on hover, press on click
    "hover:brightness-95 active:scale-[0.97] active:brightness-90";

  const radius = "rounded-[10px]"; // soft --r-btn

  const sizes = {
    sm: "h-8  px-3   text-[13px]",
    md: "h-10 px-4   text-[14px]",
    lg: "h-11 px-5   text-[15px]",
  };

  const variants = {
    primary:
      "bg-accent text-white shadow-sm font-semibold " +
      "hover:bg-accent-hover",
    secondary:
      "bg-white text-ink-800 border border-border font-medium " +
      "hover:border-border-strong hover:bg-panel-muted",
    danger:
      "bg-rose-50 text-rose-700 border border-rose-200 font-medium " +
      "hover:bg-rose-100",
    ghost:
      "text-ink-600 hover:text-ink-900 hover:bg-canvas-subtle font-medium",
    outline:
      "border border-border text-ink-700 hover:text-ink-900 " +
      "hover:border-border-strong bg-transparent font-medium",
  };

  return (
    <button
      className={twMerge(
        clsx(base, radius, sizes[size], variants[variant], className)
      )}
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
