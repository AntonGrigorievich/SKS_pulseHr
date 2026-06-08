import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "^/(api|auth|users|surveys|employee|responses|analytics|notifications|exports)": {
        target: "http://pulsehr-api:8000", // или http://pulsehr-backend:8000 в Docker
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
