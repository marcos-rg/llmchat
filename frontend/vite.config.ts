import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// `host: true` binds 0.0.0.0 so the port published by Compose actually reaches
// the dev server. `strictPort` makes a busy 5173 a hard failure instead of a
// silent shift to 5174, which would leave the container healthcheck (and
// VITE_API_BASE_URL's CORS origin) pointing at nothing.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    strictPort: true,
  },
});
