/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: "#FBF9F5",      // Warm Alabaster White background
        surface: "#FFFFFF",     // Clean card surface
        warmMuted: "#F3EFEA",   // Gentle sand/oat background
        bone: "#E7E2DA",        // Subtle tactile border
        ink: {
          DEFAULT: "#1C1917",   // Warm charcoal (stone 900)
          muted: "#78716C",     // Medium stone
          faint: "#A8A29E",     // Light stone
        },
        brand: {
          DEFAULT: "#8A4B29",   // Refined Terracotta Brick
          hover: "#723D20",
          light: "#FDF8F5",
          border: "#F1D7CA",
        },
        accent: {
          amber: "#B45309",     // Muted Warm Amber
          amberLight: "#FFFBEB",
          amberBorder: "#FDE68A",
          emerald: "#15803D",   // Deep Meadow Green
          emeraldLight: "#F0FDF4",
          emeraldBorder: "#BBF7D0",
          crimson: "#991B1B",   // Soft Terracotta Red
          crimsonLight: "#FEF2F2",
          crimsonBorder: "#FECACA",
        }
      },
      fontFamily: {
        sans: ['Vazirmatn', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'soft': '0 2px 10px -2px rgba(28, 25, 23, 0.05), 0 1px 3px -1px rgba(28, 25, 23, 0.03)',
        'lift': '0 10px 25px -4px rgba(28, 25, 23, 0.08), 0 4px 6px -2px rgba(28, 25, 23, 0.04)',
      }
    },
  },
  plugins: [],
}

