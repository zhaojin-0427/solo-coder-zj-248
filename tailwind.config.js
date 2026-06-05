/** @type {import('tailwindcss').Config} */

export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,vue}"],
  theme: {
    container: {
      center: true,
    },
    extend: {
      colors: {
        military: {
          olive: '#4A5D23',
          'olive-light': '#5E7A2E',
          'olive-dark': '#364518',
          sand: '#D4A843',
          'sand-light': '#E0BC6A',
          'sand-dark': '#B8902F',
          rust: '#8B3A2A',
          'rust-light': '#A84E3D',
          steel: '#4A6B8A',
          'steel-light': '#6288A8',
          bg: '#1A1F16',
          'bg-light': '#242B1E',
          'bg-card': '#2A3224',
          'bg-hover': '#333D2B',
        },
      },
      fontFamily: {
        display: ['Rajdhani', 'sans-serif'],
        body: ['Noto Sans SC', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
