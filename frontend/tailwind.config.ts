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
        background: "var(--background)",
        foreground: "var(--foreground)",
        gold:    { DEFAULT: "#C9A84C", light: "#E4C97A", dark: "#A8873A" },
        navy:    { DEFAULT: "#0F1F3D", light: "#1A3260", muted: "#4A5A7A" },
        success: "#22c55e",
        amber:   { DEFAULT: "#F59E0B", light: "#FCD34D" },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      boxShadow: {
        "gold-focus": "0 0 0 3px rgba(201,168,76,0.15)",
        "paper":      "inset 0 0 0 1px rgba(15,31,61,0.08)",
        "card":       "0 1px 3px rgba(0,0,0,0.4), 0 1px 2px rgba(0,0,0,0.3)",
      },
      animation: {
        shimmer: "shimmer 1.8s infinite linear",
        "slide-in-right": "slideInRight 0.25s ease-out",
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
      },
    },
  },
  plugins: [],
};
export default config;
