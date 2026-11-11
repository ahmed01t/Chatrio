import type { Config } from "tailwindcss";

/**
 * Chatrio design system
 *
 * Soft slate surfaces, indigo actions, high contrast text, and restrained motion.
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
          DEFAULT: "#F5F6FA",
          warm:    "#EFF0F8",
          subtle:  "#F0F2F8",
        },
        panel: {
          DEFAULT: "#FFFFFF",
          muted:   "#F7F8FC",
        },

        // ── Ink (near-black, warm, never pure #000) ──────────────────────
        ink: {
          900: "#171A2B",
          800: "#282C42",
          700: "#41465F",
          600: "#5A6077",
          500: "#747A90",
          400: "#969BAD",
          300: "#C6C9D4",
          200: "#E0E2E9",
          100: "#F0F2F8",
        },

        // ── Border — 12-15% ink ─────────────────────────────────────────
        border: {
          DEFAULT: "#DFE2EC",
          subtle:  "#EAECF3",
          strong:  "#C9CDE0",
        },

        // ── Accent — confident indigo ────────────────────────────────────
        accent: {
          DEFAULT: "#575BD8",
          hover:   "#484CC5",
          press:   "#3C40AE",
          light:   "#EEF0FF",
          subtle:  "#DEE1FF",
          muted:   "#7E82ED",
        },

        // ── Oatmeal — baseline bars, table stripes ───────────────────────
        oatmeal: {
          DEFAULT: "#E5E7F0",
          light:   "#F0F2F8",
          dark:    "#D4D7E5",
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

      // ── Type pairing: Space Grotesk display + Manrope interface ────────
      fontFamily: {
        display: [
          "Space Grotesk",
          "Manrope",
          "sans-serif",
        ],
        sans: [
          "Manrope",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
        mono: [
          "IBM Plex Mono",
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
        glow:     "0 0 0 3px rgba(87, 91, 216, 0.18)",
        focus:    "0 0 0 2px #FFFFFF, 0 0 0 4px #575BD8",
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
