import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const backend = "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // The dev server forwards API calls, so the browser sees a single origin (no CORS in dev).
    proxy: {
      "/api": backend,
      "/health": backend,
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/test/setup.js",
    css: false,
  },
});
