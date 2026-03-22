import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./context/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        navy:    { DEFAULT: "#0F1F3D", light: "#1A3260" },
        gold:    { DEFAULT: "#C9A84C", light: "rgba(201,168,76,0.10)", border: "rgba(201,168,76,0.25)" },
        success: { DEFAULT: "#1A6B3A", bg: "rgba(26,107,58,0.08)" },
        "warm-white": "#FAFAF8",
      },
      fontFamily: {
        sans:    ["var(--font-inter)", "ui-sans-serif", "system-ui", "sans-serif"],
        display: ["var(--font-jakarta)", "sans-serif"],
        mono:    ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      boxShadow: {
        card:       "0 2px 8px rgba(15,31,61,0.06)",
        "card-hover": "0 8px 24px rgba(15,31,61,0.10)",
        "gold-focus": "0 0 0 3px rgba(201,168,76,0.15)",
        paper:      "inset 0 0 0 1px rgba(15,31,61,0.08), 0 4px 24px rgba(15,31,61,0.08)",
      },
      borderRadius: {
        card:   "16px",
        btn:    "12px",
        input:  "8px",
      },
      animation: {
        shimmer:          "shimmer 1.8s infinite linear",
        "slide-in-right": "slideInRight 0.25s ease-out",
        "fade-in-up":     "fadeInUp 0.45s cubic-bezier(0.22,1,0.36,1) forwards",
      },
      keyframes: {
        shimmer: {
          "0%":   { backgroundPosition: "-400px 0" },
          "100%": { backgroundPosition: "400px 0"  },
        },
        slideInRight: {
          "0%":   { transform: "translateX(100%)", opacity: "0" },
          "100%": { transform: "translateX(0)",    opacity: "1" },
        },
        fadeInUp: {
          "0%":   { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)"    },
        },
      },
      maxWidth: {
        page: "1200px",
      },
    },
  },
  plugins: [],
};
export default config;
