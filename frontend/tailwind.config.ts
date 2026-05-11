import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        dream: {
          bg: "#0a0a1a",
          surface: "#12122a",
          card: "#1a1a3e",
          border: "#2a2a5e",
          accent: "#6366f1",
          purple: "#a855f7",
          glow: "#818cf8",
          text: "#e2e8f0",
          muted: "#94a3b8",
        },
      },
      backgroundImage: {
        "dream-gradient": "linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%)",
        "dream-radial": "radial-gradient(ellipse at center, #1a1a3e 0%, #0a0a1a 70%)",
      },
      boxShadow: {
        "dream-glow": "0 0 20px rgba(99, 102, 241, 0.3)",
        "dream-card": "0 4px 30px rgba(0, 0, 0, 0.4)",
      },
      animation: {
        "float": "float 6s ease-in-out infinite",
        "pulse-slow": "pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "shimmer": "shimmer 2s linear infinite",
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-10px)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
    },
  },
  plugins: [],
};
export default config;
