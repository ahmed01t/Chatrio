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
        background: "#0B0D11",
        foreground: "#F1F5F9",
        obsidian: {
          950: "#07090C",
          900: "#0B0D11",
          850: "#10131A",
          800: "#131720",
          750: "#171D27",
          700: "#1F2633",
          600: "#2B3545",
          500: "#4B5565",
          400: "#94A3B8",
          300: "#CBD5E1",
          200: "#E2E8F0",
          100: "#F1F5F9",
        },
        brand: {
          emerald: "#10B981",
          whatsapp: "#25D366",
          cyan: "#0EA5E9",
          amber: "#F59E0B",
          rose: "#EF4444",
          purple: "#8B5CF6",
        },
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      boxShadow: {
        glow: "0 0 20px -5px rgba(16, 185, 129, 0.25)",
        "glow-cyan": "0 0 20px -5px rgba(14, 165, 233, 0.25)",
        "glow-amber": "0 0 20px -5px rgba(245, 158, 11, 0.25)",
        "glow-rose": "0 0 20px -5px rgba(239, 68, 68, 0.25)",
        card: "0 4px 20px -2px rgba(0, 0, 0, 0.5)",
      },
    },
  },
  plugins: [],
};

export default config;

