import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#f7f9fb",
        surface: "#ffffff",
        "surface-subtle": "#F1F5F9",
        "border-subtle": "#E2E8F0",
        "text-primary": "#0F172A",
        "text-secondary": "#475569",
        "text-muted": "#94A3B8",
        primary: "#000000",
        secondary: "#0051d5",
        success: "#16A34A",
        warning: "#D97706",
        critical: "#DC2626",
      },
      fontFamily: {
        sans: ["Inter", "Arial", "sans-serif"],
        display: ["Manrope", "Inter", "Arial", "sans-serif"],
        mono: ["JetBrains Mono", "Consolas", "monospace"],
      },
      borderRadius: {
        DEFAULT: "0.25rem",
        lg: "0.5rem",
      },
    },
  },
  plugins: [],
};

export default config;
