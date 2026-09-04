import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Base surfaces
        background: "#f7f9fb",
        surface: "#f7f9fb",
        "surface-card": "#FFFFFF",
        "surface-subtle": "#F1F5F9",
        "surface-container-low": "#f2f4f6",
        "surface-container": "#eceef0",
        "surface-container-high": "#e6e8ea",
        "surface-container-highest": "#e0e3e5",
        "surface-container-lowest": "#ffffff",
        "surface-dim": "#d8dadc",
        "surface-variant": "#e0e3e5",
        // Borders
        "border-subtle": "#E2E8F0",
        "border-strong": "#CBD5E1",
        // Text
        "text-primary": "#0F172A",
        "text-secondary": "#475569",
        "text-muted": "#94A3B8",
        "on-surface": "#191c1e",
        "on-surface-variant": "#45464d",
        // Brand
        primary: "#000000",
        "primary-container": "#131b2e",
        "on-primary": "#ffffff",
        "on-primary-container": "#7c839b",
        secondary: "#0051d5",
        "secondary-container": "#316bf3",
        "on-secondary": "#ffffff",
        "secondary-fixed": "#dbe1ff",
        "secondary-fixed-dim": "#b4c5ff",
        // Outline
        outline: "#76777d",
        "outline-variant": "#c6c6cd",
        // Status — success
        "status-success": "#16A34A",
        "status-success-bg": "#F0FDF4",
        "status-success-border": "#BBF7D0",
        // Status — warning
        "status-warning": "#D97706",
        "status-warning-bg": "#FFFBEB",
        "status-warning-border": "#FDE68A",
        // Status — critical
        "status-critical": "#DC2626",
        "status-critical-bg": "#FEF2F2",
        "status-critical-border": "#FECACA",
        // Status — investigating
        "status-investigating": "#6366F1",
        "status-investigating-bg": "#EEF2FF",
        "status-investigating-border": "#C7D2FE",
        // Legacy aliases kept for existing code
        success: "#16A34A",
        warning: "#D97706",
        critical: "#DC2626",
      },
      fontFamily: {
        sans: ["Inter", "Arial", "sans-serif"],
        display: ["Manrope", "Inter", "Arial", "sans-serif"],
        mono: ["JetBrains Mono", "Consolas", "monospace"],
      },
      fontSize: {
        "financial-metric-lg": [
          "28px",
          { lineHeight: "36px", letterSpacing: "-0.02em", fontWeight: "700" },
        ],
        "financial-metric-md": [
          "20px",
          { lineHeight: "28px", letterSpacing: "-0.01em", fontWeight: "600" },
        ],
        "headline-xl": [
          "32px",
          { lineHeight: "40px", letterSpacing: "-0.02em", fontWeight: "700" },
        ],
        "headline-lg": [
          "24px",
          { lineHeight: "32px", letterSpacing: "-0.015em", fontWeight: "600" },
        ],
        "headline-md": [
          "20px",
          { lineHeight: "28px", letterSpacing: "-0.01em", fontWeight: "600" },
        ],
        "headline-sm": [
          "16px",
          { lineHeight: "24px", letterSpacing: "-0.005em", fontWeight: "600" },
        ],
        "body-lg": ["16px", { lineHeight: "24px", fontWeight: "400" }],
        "body-md": ["14px", { lineHeight: "20px", fontWeight: "400" }],
        "body-sm": ["13px", { lineHeight: "18px", fontWeight: "400" }],
        "label-reference": [
          "12px",
          { lineHeight: "16px", letterSpacing: "0.02em", fontWeight: "500" },
        ],
        "label-code": ["11px", { lineHeight: "14px", fontWeight: "400" }],
        caption: [
          "12px",
          { lineHeight: "16px", letterSpacing: "0.01em", fontWeight: "500" },
        ],
      },
      borderRadius: {
        DEFAULT: "0.25rem",
        sm: "0.125rem",
        lg: "0.5rem",
        xl: "0.75rem",
        full: "9999px",
      },
    },
  },
  plugins: [],
};

export default config;
