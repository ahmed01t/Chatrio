import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        canvas: {
          DEFAULT: "#FAF8F5",
          warm: "#FFF7F2",
          subtle: "#F5F0EA",
        },
        panel: {
          DEFAULT: "#FFFFFF",
          muted: "#F7F4F0",
        },
        ink: {
          900: "#111827",
          800: "#1F2937",
          700: "#334155",
          600: "#475569",
          500: "#64748B",
          400: "#94A3B8",
          300: "#CBD5E1",
          200: "#E2E8F0",
          100: "#F1F5F9",
        },
        border: {
          DEFAULT: "#ECE6DF",
          subtle: "#F2ECE5",
          strong: "#D8CFC5",
        },
        accent: {
          DEFAULT: "#EA580C", // Terracotta / warm orange (as in tasteskill app screens reference)
          hover: "#C2410C",
          light: "#FFF7ED",
          subtle: "#FFEDD5",
          chart: "#FA521A", // Vibrant chart highlight
        },
        oatmeal: {
          DEFAULT: "#EFE8E1", // Baseline chart bars in reference
          light: "#F7F2EB",
          dark: "#E3DACF",
        },
        data: {
          emerald: "#16A34A",
          green: "#25D366", // WhatsApp
          amber: "#D97706",
          rose: "#E11D48",
          sky: "#0284C7",
        },
      },
      fontFamily: {
        sans: [
          "Plus Jakarta Sans",
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      boxShadow: {
        quiet: "0 10px 25px -5px rgba(220, 100, 40, 0.04), 0 1px 3px 0 rgba(0, 0, 0, 0.02)",
        card: "0 12px 30px -8px rgba(30, 20, 10, 0.06), 0 1px 2px 0 rgba(0, 0, 0, 0.03)",
        elevated: "0 20px 40px -12px rgba(220, 90, 20, 0.08), 0 2px 6px 0 rgba(0, 0, 0, 0.04)",
        glow: "0 0 20px -3px rgba(234, 88, 12, 0.25)",
      },
    },
  },
  plugins: [],
};

export default config;
