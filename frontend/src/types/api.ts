/* DTOs mirroring the backend wire shapes in docs/backend/api-endpoints.md, named
   exactly as the API names them so payloads pass through with no mapping layer.
   Only the shapes that already exist server-side are seeded here; the run and
   auth DTOs land with the tasks that implement their endpoints. */

/** The common error envelope every non-2xx JSON response uses. */
export interface ApiErrorBody {
  error: string;
  detail: string;
}

/** `GET /api/health/`. `max_prompt_length` is null when the DB is unreachable —
 *  the endpoint reports nothing rather than falling back to a stale constant. */
export interface HealthDTO {
  status: "ok" | "error";
  db: "ok" | "error";
  broker: "ok" | "error";
  max_prompt_length: number | null;
}

/** `GET /api/settings/`. */
export interface AppSettingsDTO {
  max_prompt_length: number;
}
