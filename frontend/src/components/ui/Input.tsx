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
          <label className="block text-[13px] font-medium text-ink-700">
            {label}
          </label>
        )}

        <div className="relative flex items-center">
          {icon && (
            <div className="absolute left-3 flex items-center pointer-events-none text-ink-400">
              {icon}
            </div>
          )}
          <input
            ref={ref}
            className={twMerge(
              clsx(
                // base
                "w-full h-10 bg-white border border-border rounded-[10px]",
                "text-[14px] text-ink-900 placeholder:text-ink-400",
                "transition-all duration-150",
                // focus — terracotta ring
                "focus:outline-none focus:border-accent focus:ring-2 focus:ring-accent/15",
                // padding
                icon ? "pl-9 pr-3.5" : "px-3.5",
                // error state
                error &&
                  "border-rose-400 focus:border-rose-500 focus:ring-rose-200",
                className
              )
            )}
            {...props}
          />
        </div>

        {error && (
          <p className="text-[12px] text-rose-600 font-medium">{error}</p>
        )}
        {hint && !error && (
          <p className="text-[12px] text-ink-400">{hint}</p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";
