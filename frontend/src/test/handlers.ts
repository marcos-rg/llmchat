import { http, HttpResponse } from "msw";

import { API_BASE_URL } from "../api/client";
import type { HealthDTO } from "../types/api";

/** The healthy payload the backend's smoke test pins the key set of. */
export const healthOk: HealthDTO = {
  status: "ok",
  db: "ok",
  broker: "ok",
  max_prompt_length: 600,
};

/**
 * Default handlers, applied to every test. They are written against
 * `API_BASE_URL` rather than a hardcoded string so that changing the base URL
 * moves the mocks with the client instead of silently un-mocking every call.
 *
 * Per-test overrides go through `server.use(...)`; `setup.ts` resets them
 * between tests.
 */
export const handlers = [
  http.get(`${API_BASE_URL}/health/`, () => HttpResponse.json(healthOk)),
];
