/**
 * Design tokens of the 8-bit theme (docs/design-8bit/DESIGN.md, section 2).
 * Defined once here and as CSS variables in src/index.css; components only use these names.
 */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#000000",
        card: "#0a0d22",
        edge: "#2b3366",
        ink: { DEFAULT: "#f5f2ff", 2: "#c9c5e6", 3: "#8d89b3" },
        accent: { DEFAULT: "#8b7bff", strong: "#b3a8ff", fill: "#7a64ff" },
        ok: "#5ee08c",
        bad: "#ff6684",
        warn: "#ffbe4f",
        blue: "#5cc6ff",
        pink: "#ff92d4",
        idle: "#262c55",
      },
      fontFamily: {
        // Titles, buttons, logo, big numbers.
        display: ['"Press Start 2P"', '"Courier New"', "monospace"],
        // Interface text: menu, labels, meta, lists, chips.
        pixel: ['"Pixelify Sans"', "VT323", '"Courier New"', "monospace"],
        // Timers, page numbers, PDF/PPTX labels.
        term: ["VT323", '"Courier New"', "monospace"],
        // What the student reads to understand the task or a failure.
        plain: ["Inter", "system-ui", "-apple-system", '"Segoe UI"', "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "Menlo", "Consolas", "monospace"],
      },
      maxWidth: {
        content: "1152px", // 1120 px column + 2 x 16 px gutter
      },
    },
  },
  plugins: [],
};
