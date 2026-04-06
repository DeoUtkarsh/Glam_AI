/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"DM Sans"', 'system-ui', 'sans-serif'],
        display: ['Fraunces', 'Georgia', 'serif'],
      },
      colors: {
        glam: {
          rose: '#f4a5b8',
          plum: '#7c3aed',
          ink: '#0c0a09',
        },
      },
    },
  },
  plugins: [],
}
