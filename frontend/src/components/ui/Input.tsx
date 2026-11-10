import React from "react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, icon, ...props }, ref) => {
    return (
      <div className="w-full space-y-1.5">
        {label && (
          <label className="block text-xs font-medium text-obsidian-300">
            {label}
          </label>
        )}
        <div className="relative flex items-center">
          {icon && (
            <div className="absolute left-3.5 flex items-center pointer-events-none text-obsidian-400">
              {icon}
            </div>
          )}
          <input
            ref={ref}
            className={twMerge(
              clsx(
                "w-full bg-obsidian-900 border border-obsidian-700/80 rounded-lg py-2 text-sm text-obsidian-100 placeholder:text-obsidian-500",
                "focus:outline-none focus:border-brand-emerald focus:ring-1 focus:ring-brand-emerald transition-colors duration-150",
                icon ? "pl-10 pr-3.5" : "px-3.5",
                error && "border-brand-rose focus:border-brand-rose focus:ring-brand-rose",
                className
              )
            )}
            {...props}
          />
        </div>
        {error && <p className="text-xs text-brand-rose">{error}</p>}
      </div>
    );
  }
);

Input.displayName = "Input";

