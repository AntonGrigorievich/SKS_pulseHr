import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const apiTarget = process.env.VITE_PROXY_API_TARGET ?? "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "^/(api|auth|users|surveys|employee|responses|analytics|notifications|exports)": {
        target: apiTarget,
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
