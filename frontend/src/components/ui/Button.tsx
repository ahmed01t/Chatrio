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
    "inline-flex items-center justify-center font-medium rounded-xl transition-all duration-150 button-step focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-canvas focus:ring-accent disabled:opacity-50 disabled:cursor-not-allowed select-none";

  const sizeStyles = {
    sm: "text-xs px-2.5 py-1.5 gap-1.5 font-medium",
    md: "text-xs sm:text-sm px-3.5 py-2 gap-2 font-semibold",
    lg: "text-sm sm:text-base px-5 py-2.5 gap-2.5 font-semibold",
  };

  const variantStyles = {
    primary:
      "bg-accent hover:bg-accent-hover text-white font-semibold shadow-sm active:scale-[0.98]",
    secondary:
      "bg-white hover:bg-canvas-subtle text-ink-800 border border-border hover:border-border-strong active:scale-[0.98] shadow-sm",
    danger:
      "bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 active:scale-[0.98]",
    ghost:
      "text-ink-600 hover:text-ink-900 hover:bg-canvas-subtle active:scale-[0.98]",
    outline:
      "border border-border text-ink-700 hover:text-ink-900 hover:border-border-strong bg-transparent active:scale-[0.98]",
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
            className="animate-spin -ml-0.5 mr-2 h-3.5 w-3.5 text-current"
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
          <span>Processing...</span>
        </>
      ) : (
        children
      )}
    </button>
  );
}
