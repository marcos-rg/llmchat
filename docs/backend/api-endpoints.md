# API Endpoints

Base path: `/api/`. All endpoints except `POST /api/auth/login/` and `GET /api/auth/session/` require
an authenticated session (Django session cookie). All request/response bodies are JSON.

Common error shape:

```json
{ "error": "<machine-readable code>", "detail": "<human-readable message>" }
```

---

## Auth

### `POST /api/auth/login/`

Authenticates with email + password, starts a session.

- **Auth required:** No
- **Request body**

  ```json
  { "email": "you@company.com", "password": "••••••••" }
  ```

- **Responses**
  - `200 OK` — sets `sessionid` cookie
    ```json
    { "user": { "id": 1, "email": "you@company.com", "is_staff": false } }
    ```
  - `400 Bad Request` — missing/malformed fields
  - `401 Unauthorized` — `{ "error": "invalid_credentials", "detail": "Email or password is incorrect." }`

### `POST /api/auth/logout/`

Ends the session and purges the session's ephemeral prompt runs (see `db-schema.md`).

- **Auth required:** Yes
- **Request body:** none
- **Responses**
  - `204 No Content`
  - `401 Unauthorized` — no active session

### `GET /api/auth/session/`

Lets the SPA learn whether it already has a valid session (e.g. after a hard refresh) and doubles as
the CSRF cookie issuance point (`@ensure_csrf_cookie`). See
[`auth-contract.md`](./auth-contract.md#get-apiauthsession) for the full CSRF and cookie rationale.

- **Auth required:** No (public endpoint; response shape differs by auth state)
- **Request body:** none
- **Responses**
  - `200 OK` — active session
    ```json
    { "user": { "id": 1, "email": "you@company.com", "is_staff": false } }
    ```
  - `200 OK` — no active session (not `401` — this is an expected boot-time state)
    ```json
    { "user": null }
    ```

---

## Providers & models

### `GET /api/providers/`

Returns the provider/model catalog. Backed by a static server-side config (env-driven), not a DB
table, since providers/models are set once by an admin.

- **Auth required:** Yes
- **Responses**
  - `200 OK`
    ```json
    {
      "providers": [
        { "name": "OpenAI", "models": ["gpt-4o", "gpt-4o-mini", "gpt-4.1"] },
        { "name": "Anthropic", "models": ["claude-opus-4.5", "claude-sonnet-4.5", "claude-haiku-4.5"] }
      ]
    }
    ```

---

## System prompt library

### `GET /api/system-prompts/`

Lists the saved system prompts shown in Settings and linked from the setup screen ("Manage
library →").

- **Auth required:** Yes
- **Responses**
  - `200 OK`
    ```json
    {
      "results": [
        { "id": 1, "name": "Neutral assistant", "text": "You are a helpful, concise assistant..." },
        { "id": 2, "name": "Strict JSON output", "text": "Respond only with valid JSON..." }
      ]
    }
    ```

---

## App settings

### `GET /api/settings/`

Returns the shared app configuration used by the frontend's prompt-length counter.

- **Auth required:** Yes
- **Responses**
  - `200 OK`
    ```json
    { "max_prompt_length": 600 }
    ```

### `PATCH /api/settings/`

Updates the max prompt length. Restricted to staff/admin users.

- **Auth required:** Yes (staff/admin)
- **Request body**
  ```json
  { "max_prompt_length": 800 }
  ```
- **Responses**
  - `200 OK` — `{ "max_prompt_length": 800 }`
  - `400 Bad Request` — value outside `[100, 4000]`
  - `403 Forbidden` — authenticated but not staff

---

## Prompt runs

### `POST /api/runs/`

Creates a prompt run and fans it out into `run_count` background jobs. Returns as soon as the run
and its response placeholders are persisted — generation happens asynchronously.

- **Auth required:** Yes
- **Request body**
  ```json
  {
    "provider": "OpenAI",
    "model": "gpt-4o",
    "system_prompt": "You are a helpful, concise assistant...",
    "prompt": "Explain the difference between TCP and UDP...",
    "run_count": 4
  }
  ```
- **Validation**
  - `provider`/`model` must be a valid pair from `GET /api/providers/`
  - `run_count` integer in `[2, 5]`
  - `len(prompt) <= max_prompt_length` (current `app_settings` value)
  - `prompt` non-empty
- **Responses**
  - `201 Created`
    ```json
    {
      "id": 42,
      "provider": "OpenAI",
      "model": "gpt-4o",
      "prompt": "Explain the difference between TCP and UDP...",
      "run_count": 4,
      "responses": [
        { "id": 101, "index": 1, "status": "queued" },
        { "id": 102, "index": 2, "status": "queued" },
        { "id": 103, "index": 3, "status": "queued" },
        { "id": 104, "index": 4, "status": "queued" }
      ]
    }
    ```
  - `400 Bad Request` — `{ "error": "prompt_too_long", "detail": "Prompt exceeds 600 characters." }` (or other field errors)

### `GET /api/runs/{run_id}/`

Polled by the Run screen until every response reaches a terminal status. Includes diff tokens for
completed non-baseline responses (diffed against response `index=1`, the baseline).

- **Auth required:** Yes (must own the run)
- **Responses**
  - `200 OK`
    ```json
    {
      "id": 42,
      "provider": "OpenAI",
      "model": "gpt-4o",
      "prompt": "Explain the difference between TCP and UDP...",
      "status": "running",
      "responses": [
        {
          "id": 101,
          "index": 1,
          "is_baseline": true,
          "status": "complete",
          "response_text": "TCP is a connection-oriented protocol...",
          "diff_tokens": null,
          "error_message": null,
          "retry_count": 0
        },
        {
          "id": 102,
          "index": 2,
          "is_baseline": false,
          "status": "running",
          "response_text": null,
          "diff_tokens": null,
          "error_message": null,
          "retry_count": 0
        }
      ]
    }
    ```
  - `404 Not Found` — run doesn't exist or belongs to another user

### `POST /api/responses/{response_id}/retry/`

Re-queues a single failed response.

- **Auth required:** Yes (must own the parent run)
- **Request body:** none
- **Responses**
  - `202 Accepted` — `{ "id": 103, "status": "queued" }`
  - `404 Not Found` — response doesn't exist, isn't owned by the user, or isn't in `failed` status
