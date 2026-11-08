import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
  build: {
    // Raise the size-warning threshold — 600 KB is fine for a single-page app
    // that loads once and is then fully cached by the CDN.
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        // Split heavy vendor libs into separate cacheable chunks so the browser
        // doesn't re-download them on every deploy.
        manualChunks: {
          "vendor-react": ["react", "react-dom", "react-router-dom"],
          "vendor-query": ["@tanstack/react-query"],
          "vendor-docx": ["docx-preview"],
        },
      },
    },
  },
});
