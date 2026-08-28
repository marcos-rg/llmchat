import { defineConfig, mergeConfig } from "vitest/config";

import viteConfig from "./vite.config";

// Extends the app's own Vite config rather than restating it, so the React
// plugin, aliases and env handling used by tests are literally the ones used by
// the dev server -- a test cannot pass against a build the app never runs.
export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: "jsdom",
      setupFiles: ["./src/test/setup.ts"],
      // Only source tests. Without this, `vitest` would also try to run
      // anything under dist/ after a production build.
      include: ["src/**/*.{test,spec}.{ts,tsx}"],
      css: false,
      restoreMocks: true,
    },
  }),
);
