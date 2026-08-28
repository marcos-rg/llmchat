import { useEffect, useState } from "react";
import { apiFetch, API_BASE_URL, ApiError } from "../api/client";
import { AppShell } from "../layouts/AppShell";
import { BlueprintCorners } from "../components/BlueprintCorners";
import type { HealthDTO } from "../types/api";

type State =
  | { phase: "loading" }
  | { phase: "ready"; health: HealthDTO }
  | { phase: "error"; message: string };

/**
 * Walking-skeleton landing page. It exists to prove the full path in one render:
 * browser -> Vite-served SPA -> cross-origin call to the API -> Django ->
 * Postgres. `max_prompt_length` is the payload field worth showing because it is
 * the only one that must come out of a database *row* (the seeded AppSettings
 * singleton) rather than a constant — so a number on screen means the whole
 * chain is live.
 *
 * LLMC-RUNS-003 replaces this with the real Setup page on the same route.
 */
export function Landing() {
  const [state, setState] = useState<State>({ phase: "loading" });

  useEffect(() => {
    let cancelled = false;
    apiFetch<HealthDTO>("/health/")
      .then((health) => {
        if (!cancelled) setState({ phase: "ready", health });
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        const message =
          error instanceof ApiError
            ? `${error.code}: ${error.message}`
            : `Could not reach ${API_BASE_URL}.`;
        setState({ phase: "error", message });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <AppShell>
      <div className="tag tag-outline" style={{ marginBottom: "var(--space-3)" }}>
        Walking skeleton
      </div>
      <h1 style={{ marginBottom: "var(--space-2)" }}>Compare model consistency</h1>
      <p style={{ opacity: 0.75, fontSize: 14, marginBottom: "var(--space-6)" }}>
        The run setup form lands in LLMC-RUNS-003. Until then this page proves the stack is
        wired end to end.
      </p>

      <div className="card blueprint">
        <BlueprintCorners />
        <span className="card-kicker">GET {API_BASE_URL}/health/</span>
        {state.phase === "loading" && <p className="card-body">Contacting the API…</p>}
        {state.phase === "error" && (
          <p className="card-body" data-testid="health-error">
            {state.message}
          </p>
        )}
        {state.phase === "ready" && (
          <>
            <span className="card-title" data-testid="max-prompt-length">
              max_prompt_length: {state.health.max_prompt_length}
            </span>
            <p className="card-body">
              This value is read from the seeded AppSettings row in PostgreSQL, not from an
              environment variable.
            </p>
            <div className="card-meta">
              <span>db: {state.health.db}</span>
              <span>broker: {state.health.broker}</span>
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}
