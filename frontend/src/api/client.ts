import type { ApiErrorBody } from "../types/api";

/** Base URL of the API, e.g. `http://localhost:8000/api` (no trailing slash). */
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL.replace(/\/+$/, "");

/**
 * A non-2xx response, carrying the backend's `{error, detail}` envelope.
 *
 * `code` is the field pages should branch on — it is the backend's stable
 * machine-readable string (`invalid_credentials`, `prompt_too_long`, ...).
 * `message` is human-facing and may be reworded server-side at any time, so
 * never match on it.
 */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(status: number, code: string, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

function isErrorBody(value: unknown): value is ApiErrorBody {
  return (
    typeof value === "object" &&
    value !== null &&
    typeof (value as ApiErrorBody).error === "string"
  );
}

/**
 * Thin `fetch` wrapper: resolves the path against `API_BASE_URL`, always sends
 * the session cookie, and turns any non-2xx into an `ApiError`.
 *
 * `credentials: "include"` is unconditional rather than opt-in per call. The
 * API is cookie-session authenticated and lives on a different origin from the
 * SPA, so a call that forgets it fails as an anonymous 401 — a confusing bug to
 * chase. Its cost is that the backend's CORS config must name this exact origin
 * and allow credentials; a wildcard origin would silently drop the cookie.
 */
export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      Accept: "application/json",
      ...(init.body ? { "Content-Type": "application/json" } : {}),
      ...init.headers,
    },
  });

  // 204 carries no body; `logout` relies on this.
  const text = await response.text();
  const payload: unknown = text.length > 0 ? JSON.parse(text) : null;

  if (!response.ok) {
    if (isErrorBody(payload)) {
      throw new ApiError(response.status, payload.error, payload.detail);
    }
    throw new ApiError(
      response.status,
      "http_error",
      `Request to ${path} failed with status ${response.status}.`,
    );
  }

  return payload as T;
}
