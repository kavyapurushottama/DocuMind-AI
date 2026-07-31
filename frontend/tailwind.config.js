/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Base surfaces
        ink:       "#0F1117",
        paper:     "#F8F9FC",
        surface:   "#FFFFFF",
        muted:     "#F1F3F9",

        // Primary accent — indigo/violet
        accent:     "#5B6FFF",
        accentDark: "#4254E8",
        accentSoft: "#EEF0FF",
        accentGlow: "rgba(91,111,255,0.15)",

        // Secondary — violet
        violet:     "#8B5CF6",
        violetSoft: "#F3EEFF",

        // Semantic
        success:    "#10B981",
        warning:    "#F59E0B",
        danger:     "#EF4444",

        // Text scale
        t1: "#0F1117",
        t2: "#4B5563",
        t3: "#9CA3AF",
        t4: "#D1D5DB",
      },
      fontFamily: {
        display: ["'Space Grotesk'", "sans-serif"],
        body:    ["'Inter'",         "sans-serif"],
      },
      borderRadius: {
        "2xl": "1rem",
        "3xl": "1.25rem",
        "4xl": "1.5rem",
      },
      boxShadow: {
        card:    "0 1px 3px rgba(0,0,0,.06), 0 4px 16px rgba(0,0,0,.06)",
        glow:    "0 0 0 3px rgba(91,111,255,0.25)",
        "glow-lg":"0 0 40px rgba(91,111,255,0.18)",
        float:   "0 8px 32px rgba(0,0,0,.12)",
      },
      keyframes: {
        "fade-up": {
          "0%":   { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in": {
          "0%":   { opacity: "0" },
          "100%": { opacity: "1" },
        },
        "slide-in-right": {
          "0%":   { opacity: "0", transform: "translateX(16px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        "pulse-soft": {
          "0%, 100%": { opacity: "1" },
          "50%":      { opacity: "0.5" },
        },
        "dot-bounce": {
          "0%, 80%, 100%": { transform: "scale(0.6)", opacity: "0.4" },
          "40%":           { transform: "scale(1.0)", opacity: "1" },
        },
        "shimmer": {
          "0%":   { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        "spin-slow": {
          "0%":   { transform: "rotate(0deg)" },
          "100%": { transform: "rotate(360deg)" },
        },
      },
      animation: {
        "fade-up":         "fade-up 0.35s ease-out both",
        "fade-in":         "fade-in 0.25s ease-out both",
        "slide-in-right":  "slide-in-right 0.3s ease-out both",
        "pulse-soft":      "pulse-soft 2s ease-in-out infinite",
        "dot-bounce":      "dot-bounce 1.2s infinite ease-in-out",
        "shimmer":         "shimmer 1.8s linear infinite",
        "spin-slow":       "spin-slow 3s linear infinite",
      },
      backgroundImage: {
        "hero-gradient": "linear-gradient(135deg, #5B6FFF 0%, #8B5CF6 50%, #A855F7 100%)",
        "card-gradient": "linear-gradient(135deg, #5B6FFF 0%, #8B5CF6 100%)",
        "shimmer-bg":    "linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.6) 50%, transparent 100%)",
      },
    },
  },
  plugins: [],
};
