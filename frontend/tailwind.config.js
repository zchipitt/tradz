/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Brutalist Color Palette - Black/White + Yellow Accent
        primary: {
          DEFAULT: '#FFEB3B', // Bright yellow accent
          dark: '#FDD835',
          light: '#FFF59D',
        },

        // Backgrounds - White/Light gray
        background: '#FFFFFF',
        'bg-grid': '#F5F5F5',

        // Surface colors
        surface: {
          DEFAULT: '#FFFFFF',
          light: '#FAFAFA',
          border: '#000000',
        },

        // Brutalist accent colors (minimal)
        accent: {
          yellow: '#FFEB3B',
          black: '#000000',
          white: '#FFFFFF',
          gray: '#9CA3AF',
          'gray-light': '#E5E5E5',
        },

        // Status colors - High contrast
        status: {
          success: '#22C55E',
          error: '#EF4444',
          warning: '#F59E0B',
          info: '#3B82F6',
        },

        // Text colors
        text: {
          DEFAULT: '#000000',
          primary: '#000000',
          muted: '#6B7280',
          light: '#9CA3AF',
          inverse: '#FFFFFF',
        },

        // Score colors
        score: {
          excellent: '#22C55E',
          good: '#4ADE80',
          moderate: '#F59E0B',
          low: '#F97316',
          poor: '#EF4444',
        },

        // Price movement
        positive: '#22C55E',
        negative: '#EF4444',
        neutral: '#6B7280',
      },
      fontFamily: {
        mono: ['Space Mono', 'Fira Code', 'JetBrains Mono', 'Consolas', 'Monaco', 'monospace'],
        sans: ['Space Mono', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        'xs': ['0.75rem', { lineHeight: '1.25rem' }],
        'sm': ['0.875rem', { lineHeight: '1.375rem' }],
        'base': ['1rem', { lineHeight: '1.6rem' }],
        'lg': ['1.125rem', { lineHeight: '1.75rem' }],
        'xl': ['1.25rem', { lineHeight: '1.875rem' }],
        '2xl': ['1.5rem', { lineHeight: '2rem' }],
        '3xl': ['2rem', { lineHeight: '2.5rem' }],
        '4xl': ['2.5rem', { lineHeight: '3rem' }],
      },
      borderRadius: {
        'none': '0',
        'sm': '2px',
        DEFAULT: '2px',
        'md': '4px',
      },
      borderWidth: {
        DEFAULT: '1px',
        '0': '0',
        '1': '1px',
        '2': '2px',
        '3': '3px',
      },
      boxShadow: {
        'none': 'none',
        'brutal': '4px 4px 0 0 #000000',
        'brutal-sm': '2px 2px 0 0 #000000',
        'brutal-yellow': '4px 4px 0 0 #FFEB3B',
      },
      spacing: {
        '18': '4.5rem',
        '22': '5.5rem',
      },
    },
  },
  plugins: [],
}
