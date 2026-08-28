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
      // Non-interactive by default so a bare `npm test` cannot hang CI or
      // `make test-frontend`. Keeping the script itself as plain `vitest` means
      // `npm test -- --run` (what docs/infra/testing.md specifies) still works;
      // baking --run into the script instead makes that invocation die with
      // "Expected a single value for option --run". Watch mode is `npm run
      // test:watch`.
      watch: false,
      setupFiles: ["./src/test/setup.ts"],
      // Only source tests. Without this, `vitest` would also try to run
      // anything under dist/ after a production build.
      include: ["src/**/*.{test,spec}.{ts,tsx}"],
      css: false,
      restoreMocks: true,
    },
  }),
);
