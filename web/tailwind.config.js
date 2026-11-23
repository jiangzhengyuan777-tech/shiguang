/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        cream: '#FDFBF7',
        paper: '#FFFFFF',
        ink: '#2B2118',
        muted: '#8A7E70',
        line: '#F0E6DA',
        coral: {
          DEFAULT: '#FF6B4A',
          dark: '#E85535',
          light: '#FFE8E2',
          soft: '#FFF1ED',
        },
        amber: {
          DEFAULT: '#FFB84D',
          light: '#FFF4E0',
        },
        sage: '#7BA05B',
      },
      fontFamily: {
        serif: ['"Noto Serif SC"', 'Songti SC', 'SimSun', 'Georgia', 'serif'],
        sans: ['-apple-system', 'BlinkMacSystemFont', '"PingFang SC"', '"Microsoft YaHei"', 'sans-serif'],
      },
      boxShadow: {
        soft: '0 2px 12px rgba(43, 33, 24, 0.06)',
        lift: '0 8px 28px rgba(43, 33, 24, 0.10)',
      },
      borderRadius: {
        card: '16px',
      },
    },
  },
  plugins: [],
}
