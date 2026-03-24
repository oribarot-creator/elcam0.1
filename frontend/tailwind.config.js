/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './public/index.html',
    './src/**/*.{js,jsx,ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        ember: {
          50: '#fff8f2',
          100: '#ffeddc',
          200: '#ffd8b3',
          500: '#ea7a35',
          700: '#b44b1f',
          900: '#6e2a14',
        },
      },
      boxShadow: {
        card: '0 14px 40px rgba(14, 23, 40, 0.12)',
      },
    },
  },
  plugins: [],
}

