import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { setupServer } from "msw/node";
import { afterAll, afterEach, beforeAll } from "vitest";

import { handlers } from "./handlers";

/** The shared msw server. Import it in a test to override a handler. */
export const server = setupServer(...handlers);

// `onUnhandledRequest: "error"` is the point of the whole setup: any fetch a
// component makes that no handler covers fails the test loudly, instead of
// escaping to the real network and making the suite depend on a running backend.
beforeAll(() => server.listen({ onUnhandledRequest: "error" }));

afterEach(() => {
  server.resetHandlers();
  cleanup();
});

afterAll(() => server.close());
