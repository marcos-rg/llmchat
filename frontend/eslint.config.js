import js from "@eslint/js";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import tseslint from "typescript-eslint";

/**
 * Flat config (ESLint 9). Formatting is Prettier's job, not ESLint's -- no
 * stylistic rules are enabled here, so the two can never disagree about the same
 * line.
 */
export default tseslint.config(
  { ignores: ["dist", "coverage", ".vite", "node_modules"] },
  {
    files: ["**/*.{ts,tsx}"],
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    languageOptions: {
      ecmaVersion: 2022,
      globals: globals.browser,
    },
    plugins: {
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      "react-refresh/only-export-components": ["warn", { allowConstantExport: true }],
    },
  },
  {
    // Test files run in Node (msw/node, vitest globals) and legitimately export
    // non-components such as the shared `server`.
    files: ["**/*.{test,spec}.{ts,tsx}", "src/test/**/*.ts"],
    languageOptions: { globals: { ...globals.browser, ...globals.node } },
    rules: { "react-refresh/only-export-components": "off" },
  },
  {
    files: ["*.config.{js,ts}"],
    languageOptions: { globals: globals.node },
  },
);
