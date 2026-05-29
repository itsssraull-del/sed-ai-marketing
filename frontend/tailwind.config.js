/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // SED Energy Brand Colors
        sed: {
          orange:       "#F26522",
          "orange-dark":  "#D4521A",
          "orange-light": "#FF7A3D",
          "orange-glow":  "rgba(242,101,34,0.15)",
          dark:         "#0F0F0F",
          surface:      "#181818",
          "surface-2":  "#202020",
          "surface-3":  "#2A2A2A",
          border:       "#2A2A2A",
          "border-light":"#333333",
          charcoal:     "#4A4A4A",
          "grey-mid":   "#888888",
          "grey-light": "#AAAAAA",
          white:        "#FFFFFF",
        },
        // Status colors
        success:  "#22C55E",
        warning:  "#F59E0B",
        danger:   "#EF4444",
        info:     "#3B82F6",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      borderRadius: {
        "4xl": "2rem",
      },
      boxShadow: {
        "sed":    "0 4px 24px rgba(232, 90, 12, 0.15)",
        "card":   "0 2px 16px rgba(0, 0, 0, 0.08)",
        "card-hover": "0 8px 32px rgba(0, 0, 0, 0.14)",
      },
      animation: {
        "pulse-orange": "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "fade-in":      "fadeIn 0.3s ease-out",
        "slide-up":     "slideUp 0.3s ease-out",
      },
      keyframes: {
        fadeIn:  { from: { opacity: 0 }, to: { opacity: 1 } },
        slideUp: { from: { opacity: 0, transform: "translateY(10px)" }, to: { opacity: 1, transform: "translateY(0)" } },
      },
    },
  },
  plugins: [],
};
