import React from "react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "critical" | "warning" | "active" | "success" | "purple" | "neutral" | "terracotta";
  size?: "sm" | "md";
  dot?: boolean;
}

export function Badge({
  className,
  variant = "neutral",
  size = "md",
  dot = false,
  children,
  ...props
}: BadgeProps) {
  const sizeStyles = {
    sm: "text-[11px] px-2 py-0.5 gap-1 font-semibold",
    md: "text-xs px-2.5 py-1 gap-1.5 font-semibold",
  };

  const variantStyles = {
    terracotta: "bg-accent-light border border-accent-subtle text-accent",
    critical: "bg-rose-50 border border-rose-200 text-rose-700",
    warning: "bg-amber-50 border border-amber-200 text-amber-700",
    active: "bg-sky-50 border border-sky-200 text-sky-700",
    success: "bg-emerald-50 border border-emerald-200 text-emerald-700",
    purple: "bg-purple-50 border border-purple-200 text-purple-700",
    neutral: "bg-canvas-subtle border border-border text-ink-700",
  };

  const dotColors = {
    terracotta: "bg-accent",
    critical: "bg-rose-500",
    warning: "bg-amber-500",
    active: "bg-sky-500",
    success: "bg-emerald-500",
    purple: "bg-purple-500",
    neutral: "bg-ink-400",
  };

  return (
    <span
      className={twMerge(
        clsx(
          "inline-flex items-center rounded-full leading-none tracking-tight",
          sizeStyles[size],
          variantStyles[variant],
          className
        )
      )}
      {...props}
    >
      {dot && <span className={clsx("w-1.5 h-1.5 rounded-full shrink-0", dotColors[variant])} />}
      {children}
    </span>
  );
}
