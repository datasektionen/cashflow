import tailwindcss from "@tailwindcss/vite";
import { devtools } from "@tanstack/devtools-vite";
import { tanstackStart } from "@tanstack/react-start/plugin/vite";
import viteReact from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Paths the Go server owns. In production it serves the SPA itself; in dev
// Vite forwards these so the session cookie lives on the Vite origin.
const SERVER_PATHS = ["/api", "/login", "/auth", "/logout", "/fortnox", "/files", "/healthz"];
const serverUrl = process.env.CASHFLOW_SERVER_URL ?? "http://localhost:3000";

export default defineConfig({
  server: {
    port: 5173,
    strictPort: true,
    proxy: Object.fromEntries(SERVER_PATHS.map((path) => [path, { target: serverUrl }])),
  },
  resolve: { tsconfigPaths: true },
  plugins: [
    // Dev only: devtools event bus and click-to-source. Stripped from builds.
    devtools(),
    tailwindcss(),
    // SPA mode: no SSR. The build emits a static shell that the Go binary embeds.
    tanstackStart({ spa: { enabled: true } }),
    viteReact(),
  ],
});
