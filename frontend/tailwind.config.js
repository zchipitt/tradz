/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Signal score colors
        score: {
          excellent: '#22c55e', // 80-100
          good: '#84cc16',      // 60-79
          moderate: '#eab308',  // 40-59
          low: '#f97316',       // 20-39
          poor: '#ef4444',      // 0-19
        },
        // Price movement colors
        positive: '#22c55e',
        negative: '#ef4444',
        neutral: '#71717a',
      },
    },
  },
  plugins: [],
}
