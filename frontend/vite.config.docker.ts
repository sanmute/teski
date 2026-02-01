import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

// Docker-specific Vite config with container networking
// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    host: "0.0.0.0",
    port: 5173,
    watch: {
      usePolling: true, // Required for Docker volume mounts on some systems
    },
    proxy: {
      "/api": {
        target: "http://legacy:8100",
        changeOrigin: true,
      },
      "/tasks": {
        target: "http://legacy:8100",
        changeOrigin: true,
      },
      "/study": {
        target: "http://legacy:8100",
        changeOrigin: true,
      },
      "/explanations": {
        target: "http://legacy:8100",
        changeOrigin: true,
      },
      "/onboarding": {
        target: "http://legacy:8100",
        changeOrigin: true,
      },
      "/feedback": {
        target: "http://api:8000",
        changeOrigin: true,
      },
      "/analytics": {
        target: "http://api:8000",
        changeOrigin: true,
      },
      "/deep": {
        target: "http://api:8000",
        changeOrigin: true,
      },
      "/prefs": {
        target: "http://api:8000",
        changeOrigin: true,
      },
    },
  },
  plugins: [react(), mode === "development" && componentTagger()].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
}));
