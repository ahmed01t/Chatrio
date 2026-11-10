import React from "react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
  icon?: React.ReactNode;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, hint, icon, ...props }, ref) => {
    return (
      <div className="w-full space-y-1.5">
        {label && (
          <label
            className="block text-[13px] font-medium"
            style={{ color: "var(--ink-3)" }}
          >
            {label}
          </label>
        )}

        <div className="relative flex items-center">
          {icon && (
            <div
              className="absolute left-3 flex items-center pointer-events-none"
              style={{ color: "var(--ink-6)" }}
            >
              {icon}
            </div>
          )}
          <input
            ref={ref}
            style={{
              backgroundColor: "var(--g-panel)",
              borderColor: error ? undefined : "var(--line)",
              color: "var(--ink)",
            }}
            className={twMerge(
              clsx(
                "w-full h-10 border rounded-[10px]",
                "text-[14px] placeholder:text-ink-400",
                "transition-all duration-150",
                "focus:outline-none focus:ring-2 focus:ring-accent/20",
                icon ? "pl-9 pr-3.5" : "px-3.5",
                error && "border-rose-400 focus:border-rose-400",
                className
              )
            )}
            onFocus={(e) => {
              if (!error) e.currentTarget.style.borderColor = "var(--action)";
            }}
            onBlur={(e) => {
              if (!error) e.currentTarget.style.borderColor = "var(--line)";
            }}
            {...props}
          />
        </div>

        {error && (
          <p className="text-[12px] text-rose-500 font-medium">{error}</p>
        )}
        {hint && !error && (
          <p className="text-[12px]" style={{ color: "var(--ink-6)" }}>
            {hint}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";
