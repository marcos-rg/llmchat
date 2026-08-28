import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";

/**
 * Authenticated shell (Setup / Run / Settings): full-viewport flex column with a
 * fixed-height nav and a `<main>` that grows to fill the rest.
 *
 * `width` picks the content container from docs/frontend/layouts.md:
 * - "narrow" — 760px centered column, for form/list pages (Setup, Settings).
 * - "wide"   — no max-width on `<main>`, so the Run screen's response row can
 *              scroll horizontally edge to edge while its header aligns to
 *              1400px on its own.
 *
 * The active link is marked by `NavLink`'s own `aria-current="page"`, which is
 * also the styling hook (`.nav a[aria-current='page']`) — there is deliberately
 * no parallel "active" class to keep in sync with it.
 */
export function AppShell({
  children,
  userEmail = null,
  width = "narrow",
}: {
  children: ReactNode;
  userEmail?: string | null;
  width?: "narrow" | "wide";
}) {
  const mainStyle =
    width === "narrow"
      ? {
          flex: 1,
          maxWidth: 760,
          width: "100%",
          margin: "0 auto",
          padding: "var(--space-8) var(--space-4)",
        }
      : { flex: 1, padding: "var(--space-6) var(--space-4)" };

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <nav className="nav" style={{ borderBottom: "1px solid var(--color-divider)" }}>
        <span className="nav-brand">LLMChat</span>
        {/* `end` keeps "New run" from matching every nested path. */}
        <NavLink to="/" end>
          New run
        </NavLink>
        <NavLink to="/settings">Settings</NavLink>
        {/* Rendered even while empty so the nav does not reflow once
            LLMC-AUTH-003 supplies the session's email. */}
        <span style={{ marginLeft: "auto", fontSize: 13, opacity: 0.65 }}>
          {userEmail ?? ""}
        </span>
        <button type="button" className="btn btn-ghost" disabled>
          Log out
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            aria-hidden="true"
          >
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
            <path d="M16 17l5-5-5-5" />
            <path d="M21 12H9" />
          </svg>
        </button>
      </nav>
      <main style={mainStyle}>{children}</main>
    </div>
  );
}
