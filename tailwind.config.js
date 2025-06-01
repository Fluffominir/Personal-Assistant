
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./static/**/*.{html,js}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Figtree', 'ui-sans-serif', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'Noto Sans', 'sans-serif'],
        mono: ['IBM Plex Mono', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', 'monospace']
      },
      colors: {
        'atlas': {
          'violet': 'var(--atlas-violet)',
          'rose': 'var(--atlas-rose)',
          'teal': 'var(--atlas-teal)',
          'glass': 'var(--atlas-glass)',
          'glass-dark': 'var(--atlas-glass-dark)',
          'accent': 'var(--atlas-accent)',
          'secondary': 'var(--atlas-secondary)'
        }
      }
    },
  },
  plugins: [],
}
