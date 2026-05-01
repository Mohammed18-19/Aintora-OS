/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#f0f4ff',
          100: '#e0e9ff',
          200: '#c1d3ff',
          300: '#93b0ff',
          400: '#5d82ff',
          500: '#3355ff',
          600: '#1a32f5',
          700: '#1525e0',
          800: '#1620b5',
          900: '#171f8e',
          950: '#111462',
        },
        accent: {
          DEFAULT: '#e91e8c',
          light: '#ff4db3',
          dark: '#c0166f',
        },
        dark: {
          bg:      '#0a0a14',
          card:    '#12121f',
          border:  '#1e1e32',
          muted:   '#6b7280',
        },
      },
      fontFamily: {
        sans:    ['Plus Jakarta Sans', 'system-ui', 'sans-serif'],
        display: ['Syne', 'sans-serif'],
        mono:    ['JetBrains Mono', 'monospace'],
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'mesh-brand': 'radial-gradient(at 40% 20%, hsla(228,100%,66%,0.15) 0px, transparent 50%), radial-gradient(at 80% 0%, hsla(317,100%,52%,0.10) 0px, transparent 50%)',
      },
      animation: {
        'fade-in': 'fadeIn 0.4s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: { from: { opacity: '0' }, to: { opacity: '1' } },
        slideUp: { from: { opacity: '0', transform: 'translateY(12px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
      },
    },
  },
  plugins: [],
}
