import type { Config } from "tailwindcss";

/**
 * Chatrio design system
 *
 * Obsidian surfaces, emerald actions, high contrast text, and restrained motion.
 */
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
        // ── Ground ──────────────────────────────────────────────────────────
        canvas: {
          DEFAULT: "#FAFAF9",   // main ground — tasteskill warm white
          warm:    "#FFF8F4",   // ambient warm tint
          subtle:  "#F4F0EB",   // section alt ground
        },
        panel: {
          DEFAULT: "#FFFFFF",   // quiet panels (cards, tables)
          muted:   "#F9F7F4",   // muted panel variant
        },

        // ── Ink (near-black, warm, never pure #000) ──────────────────────
        ink: {
          900: "#18181B",  // primary text, headings
          800: "#27272A",  // secondary headings
          700: "#3F3F46",  // body
          600: "#52525B",  // secondary body
          500: "#71717A",  // muted / labels
          400: "#A1A1AA",  // placeholder
          300: "#D4D4D8",  // dividers
          200: "#E4E4E7",  // hairlines
          100: "#F4F4F5",  // subtle bg
        },

        // ── Border — 12-15% ink ─────────────────────────────────────────
        border: {
          DEFAULT: "#E6E0D8",   // standard hairline
          subtle:  "#EDE8E2",   // very light
          strong:  "#D5CEC5",   // emphasis
        },

        // ── Accent — WhatsApp emerald ─────────────────────────────────────
        accent: {
          DEFAULT: "#10B981",   // WhatsApp emerald primary action
          hover:   "#059669",
          press:   "#047857",
          light:   "#D1FAE5",
          subtle:  "#A7F3D0",
          muted:   "#34D399",
        },

        // ── Oatmeal — baseline bars, table stripes ───────────────────────
        oatmeal: {
          DEFAULT: "#EDE6DC",
          light:   "#F5F0E8",
          dark:    "#DDD3C5",
        },

        // ── Data colours (used sparingly) ───────────────────────────────
        data: {
          emerald: "#16A34A",   // positive deltas
          green:   "#22C55E",   // success states
          amber:   "#D97706",   // warnings
          rose:    "#E11D48",   // errors / negative
          sky:     "#0284C7",   // info
          whatsapp: "#25D366",  // WhatsApp brand green
        },
      },

      // ── Type pairing (tasteskill.dev: Instrument Serif + Inter) ─────────
      fontFamily: {
        display: [
          "Instrument Serif",
          "Georgia",
          "Times New Roman",
          "serif",
        ],
        sans: [
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
        mono: [
          "JetBrains Mono",
          "Fira Code",
          "ui-monospace",
          "SFMono-Regular",
          "monospace",
        ],
      },

      // ── Spacing scale (4-step system) ───────────────────────────────────
      spacing: {
        "s1": "4px",
        "s2": "8px",
        "s3": "12px",
        "s4": "16px",
        "s5": "24px",
        "s6": "32px",
        "s7": "48px",
        "s8": "64px",
        "s9": "96px",
        "s10": "128px",
      },

      // ── Radius scale (soft: 8/12/20) ─────────────────────────────────
      borderRadius: {
        "r-sm":  "8px",   // controls
        "r-md":  "12px",  // panels
        "r-lg":  "20px",  // cards, frames
        "r-btn": "10px",  // buttons
        "r-pill": "9999px",
      },

      // ── Box shadows (warm, soft) ──────────────────────────────────────
      boxShadow: {
        // quiet panel — same as tasteskill cards
        quiet:    "0 1px 2px 0 rgba(24, 24, 27, 0.04), 0 1px 10px -4px rgba(24, 24, 27, 0.06)",
        card:     "0 4px 16px -4px rgba(24, 24, 27, 0.08), 0 1px 2px 0 rgba(24, 24, 27, 0.03)",
        elevated: "0 8px 24px -6px rgba(24, 24, 27, 0.10), 0 2px 4px 0 rgba(24, 24, 27, 0.04)",
        // Emerald focus / glow
        glow:     "0 0 0 3px rgba(16, 185, 129, 0.18)",
        focus:    "0 0 0 2px #0B0D11, 0 0 0 4px #10B981",
      },

      // ── Keyframe animations ──────────────────────────────────────────
      keyframes: {
        "fade-up": {
          "0%":   { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)"    },
        },
        "fade-in": {
          "0%":   { opacity: "0" },
          "100%": { opacity: "1" },
        },
        "scale-in": {
          "0%":   { opacity: "0", transform: "scale(0.97)" },
          "100%": { opacity: "1", transform: "scale(1)"    },
        },
        "bar-rise": {
          "0%":   { transform: "scaleY(0)", transformOrigin: "bottom" },
          "100%": { transform: "scaleY(1)", transformOrigin: "bottom" },
        },
        shimmer: {
          "0%":   { backgroundPosition: "-400px 0" },
          "100%": { backgroundPosition: "400px 0"  },
        },
      },
      animation: {
        "fade-up":    "fade-up 0.4s cubic-bezier(0.16, 1, 0.3, 1) both",
        "fade-in":    "fade-in 0.3s ease both",
        "scale-in":   "scale-in 0.25s cubic-bezier(0.16, 1, 0.3, 1) both",
        "bar-rise":   "bar-rise 0.6s cubic-bezier(0.16, 1, 0.3, 1) both",
        shimmer:      "shimmer 1.6s linear infinite",
      },
    },
  },
  plugins: [],
};

export default config;
