import React from "react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "critical" | "warning" | "active" | "success" | "purple" | "neutral";
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
    sm: "text-[11px] px-2 py-0.5 gap-1 font-medium",
    md: "text-xs px-2.5 py-1 gap-1.5 font-medium",
  };

  const variantStyles = {
    critical: "bg-red-500/10 border border-red-500/30 text-red-400",
    warning: "bg-amber-500/10 border border-amber-500/30 text-amber-400",
    active: "bg-sky-500/10 border border-sky-500/30 text-sky-400",
    success: "bg-emerald-500/10 border border-emerald-500/30 text-emerald-400",
    purple: "bg-purple-500/10 border border-purple-500/30 text-purple-400",
    neutral: "bg-obsidian-800 border border-obsidian-700 text-obsidian-300",
  };

  const dotColors = {
    critical: "bg-red-400",
    warning: "bg-amber-400",
    active: "bg-sky-400 animate-pulse",
    success: "bg-emerald-400",
    purple: "bg-purple-400",
    neutral: "bg-obsidian-400",
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

