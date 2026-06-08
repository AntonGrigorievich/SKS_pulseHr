import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://api:8000",
      "/auth": "http://api:8000",
      "/users": "http://api:8000",
      "/surveys": "http://api:8000",
      "/employee": "http://api:8000",
      "/responses": "http://api:8000",
      "/analytics": "http://api:8000",
      "/notifications": "http://api:8000",
      "/exports": "http://api:8000",
    }
  }
});

