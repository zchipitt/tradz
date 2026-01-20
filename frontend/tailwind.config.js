/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Robinhood-style Color Palette
        primary: {
          DEFAULT: '#00C805', // Robinhood Green
          light: '#E8F9E8',
          dark: '#00A004',
        },
        background: '#FFFFFF',
        surface: '#F5F5F5',
        border: '#E5E5E5',
        text: {
          DEFAULT: '#1A1A1A',
          muted: '#6B7280',
          light: '#9CA3AF',
        },

        // Score colors
        score: {
          excellent: '#00C805',
          good: '#84cc16',
          moderate: '#eab308',
          low: '#f97316',
          poor: '#ef4444',
        },
        // Price movement
        positive: '#00C805',
        negative: '#FF5000',
        neutral: '#6B7280',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
