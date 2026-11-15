import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev-server API target; defaults to the local backend on :8000. Set FIXIT_API_TARGET to preview against another one.
const api = process.env.FIXIT_API_TARGET || "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  server: { host: true, proxy: { "/api": api } },
});
