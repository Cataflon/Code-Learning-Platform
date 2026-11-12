/** Design tokens for mockup variant D (dark theme). Defined once, reused everywhere. */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0e0f1a", // page background, almost black
        header: "#161826",
        surface: "#171927", // cards
        raised: "#1f2133", // inputs, table headers, inner boxes
        line: "#2a2d45", // borders
        ink: "#ffffff",
        muted: "#9a9cb5",
        faint: "#6b6e8a",
        accent: {
          DEFAULT: "#5b57e0", // primary buttons
          hover: "#6a66ee",
          soft: "#b4b1ff", // links, chip text
          tint: "#25264a", // chip / active nav background
        },
        pass: { DEFAULT: "#4ade80", tint: "#14301f", line: "#1f5a35" },
        fail: { DEFAULT: "#f87171", tint: "#3a1519", line: "#7a2a2f" },
        warn: { DEFAULT: "#fbbf24", tint: "#33270b", line: "#6b4f10" },
        info: { DEFAULT: "#60a5fa", tint: "#13233d", line: "#234a80" },
        hidden: { DEFAULT: "#c084fc", tint: "#2c1a47" },
        idle: "#2b2d44", // empty verdict square
      },
      fontFamily: {
        sans: ["Poppins", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      borderRadius: {
        card: "14px",
      },
    },
  },
  plugins: [],
};
