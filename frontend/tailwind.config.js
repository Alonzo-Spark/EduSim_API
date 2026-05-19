/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        physics: {
          bg: "#05080f",
          panel: "#0b0f19",
          card: "rgba(15, 23, 42, 0.85)",
          neonCyan: "#00eeff",
          neonMagenta: "#f43f5e",
          neonYellow: "#fbbf24",
          neonGreen: "#10b981",
          border: "#1e293b",
          textMuted: "#64748b"
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace']
      }
    },
  },
  plugins: [],
}
