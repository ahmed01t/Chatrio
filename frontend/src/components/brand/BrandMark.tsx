import { clsx } from "clsx";
import type { JSX } from "react";

type BrandMarkSize = "small" | "medium" | "large";

interface BrandMarkProps {
  size?: BrandMarkSize;
  className?: string;
}

const sizeClasses: Record<BrandMarkSize, string> = {
  small: "h-9 w-9 rounded-xl",
  medium: "h-10 w-10 rounded-xl",
  large: "h-12 w-12 rounded-2xl",
};

export function BrandMark({ size = "medium", className }: BrandMarkProps): JSX.Element {
  return (
    <span
      aria-hidden="true"
      className={clsx("grid shrink-0 place-items-center bg-accent", sizeClasses[size], className)}
    >
      <svg viewBox="0 0 40 40" width={size === "small" ? 19 : 22} height={size === "small" ? 19 : 22} fill="none" style={{ color: "var(--color-accent-ink)" }}>
        <path d="M20 7.75c-6.9 0-12.5 4.62-12.5 10.33 0 2.55 1.12 4.88 2.98 6.69l-.9 6.08 6.07-3.05c1.35.39 2.82.61 4.35.61 6.9 0 12.5-4.62 12.5-10.33S26.9 7.75 20 7.75Z" stroke="currentColor" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M14.75 17.25h10.5M14.75 21.5h6.25" stroke="currentColor" strokeWidth="2.1" strokeLinecap="round" />
      </svg>
    </span>
  );
}
