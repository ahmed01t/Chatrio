"use client";

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
  const baseStyles =
    "inline-flex items-center justify-center font-medium rounded-lg transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-obsidian-950 disabled:opacity-50 disabled:cursor-not-allowed";

  const sizeStyles = {
    sm: "text-xs px-2.5 py-1.5 gap-1.5",
    md: "text-sm px-3.5 py-2 gap-2",
    lg: "text-base px-5 py-2.5 gap-2.5",
  };

  const variantStyles = {
    primary:
      "bg-brand-emerald hover:bg-emerald-400 text-obsidian-950 font-semibold shadow-glow focus:ring-brand-emerald active:scale-[0.98]",
    secondary:
      "bg-obsidian-800 hover:bg-obsidian-750 text-obsidian-200 border border-obsidian-700 hover:border-obsidian-600 focus:ring-obsidian-500",
    danger:
      "bg-brand-rose/20 hover:bg-brand-rose/30 text-rose-300 border border-brand-rose/40 shadow-glow-rose focus:ring-brand-rose",
    ghost:
      "text-obsidian-400 hover:text-obsidian-100 hover:bg-obsidian-800/60 focus:ring-obsidian-500",
    outline:
      "border border-obsidian-700 text-obsidian-300 hover:text-white hover:border-obsidian-500 bg-transparent",
  };

  return (
    <button
      className={twMerge(clsx(baseStyles, sizeStyles[size], variantStyles[variant], className))}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <>
          <svg
            className="animate-spin -ml-0.5 mr-2 h-4 w-4 text-current"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8v8H4z"
            />
          </svg>
          Loading...
        </>
      ) : (
        children
      )}
    </button>
  );
}

