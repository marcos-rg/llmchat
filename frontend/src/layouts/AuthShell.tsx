import type { ReactNode } from "react";

/**
 * Unauthenticated shell (Login): one full-viewport flex container centering a
 * single card. Deliberately has no nav — there is nothing to navigate to before
 * a session exists.
 */
export function AuthShell({ children }: { children: ReactNode }) {
  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "var(--space-4)",
      }}
    >
      {children}
    </div>
  );
}
