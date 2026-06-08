import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
      "/auth": "http://localhost:8000",
      "/users": "http://localhost:8000",
      "/surveys": "http://localhost:8000",
      "/employee": "http://localhost:8000",
      "/responses": "http://localhost:8000",
      "/analytics": "http://localhost:8000",
      "/notifications": "http://localhost:8000",
      "/exports": "http://localhost:8000"
    }
  }
});

