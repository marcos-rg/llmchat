import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import { Landing } from "../pages/Landing";
import { API_BASE_URL } from "../api/client";
import { server } from "../test/setup";

/**
 * The frontend half of the walking-skeleton smoke test. It renders the landing
 * route -- which is `AppShell` plus the health card -- against an msw-mocked
 * `/health/`, so it proves the shell renders, the route's data path works, and
 * no real network call happens.
 *
 * It renders `<Landing />` inside a `MemoryRouter` rather than `<App />`,
 * because `App` owns a `BrowserRouter` and nesting routers throws. When
 * LLMC-AUTH-003 adds the route guard, the guard is what gets a router-level
 * test; this one stays about the shell.
 */
function renderLanding() {
  return render(
    <MemoryRouter initialEntries={["/"]}>
      <Landing />
    </MemoryRouter>,
  );
}

describe("the landing route in the app shell", () => {
  it("renders the nav and the mocked max_prompt_length", async () => {
    renderLanding();

    // Shell first: nav links exist before any data arrives.
    expect(screen.getByText("LLMChat")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "New run" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Settings" })).toBeInTheDocument();

    expect(await screen.findByTestId("max-prompt-length")).toHaveTextContent(
      "max_prompt_length: 600",
    );
  });

  it("marks the active nav link with aria-current, not a class", async () => {
    renderLanding();
    await screen.findByTestId("max-prompt-length");

    expect(screen.getByRole("link", { name: "New run" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.getByRole("link", { name: "Settings" })).not.toHaveAttribute("aria-current");
  });

  it("shows the error state when the API call fails", async () => {
    server.use(
      http.get(`${API_BASE_URL}/health/`, () =>
        HttpResponse.json({ error: "boom", detail: "backend is down" }, { status: 503 }),
      ),
    );

    renderLanding();

    expect(await screen.findByTestId("health-error")).toHaveTextContent(
      "boom: backend is down",
    );
  });
});
