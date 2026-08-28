# Sequence Diagrams

Each diagram covers one user-triggered action visible in the UI mockups (`docs/UI/`). Lifelines:

- **Browser** — the React SPA
- **API** — Django (DRF) views
- **DB** — PostgreSQL
- **Broker** — Redis
- **Worker** — Django-Q2 background worker process
- **LangChain** — orchestration layer inside the worker, calling the OpenAI/Anthropic SDKs

---

## 1. Log in

Corresponds to the login screen. Django's session auth is used (cookie-based), matching
"Authentication is required for all prompt/response functionality."

```mermaid
sequenceDiagram
    actor U as User
    participant B as Browser
    participant A as API
    participant DB as PostgreSQL

    U->>B: Enter email + password, click "Log in"
    B->>A: POST /api/auth/login/ {email, password}
    A->>DB: Look up User by email
    DB-->>A: User row (hashed password)
    A->>A: Verify password (Django auth)
    alt credentials valid
        A->>DB: Create Session
        A-->>B: 200 OK, Set-Cookie: sessionid + {user}
        B->>B: Navigate to "New run" screen
    else invalid credentials
        A-->>B: 401 Unauthorized {error}
        B->>U: Show inline error
    end
```

---

## 2. Log out

Also enforces the ephemeral-data requirement: any prompt runs created in this session are purged
so nothing survives logout (see `db-schema.md` for the cascade).

```mermaid
sequenceDiagram
    actor U as User
    participant B as Browser
    participant A as API
    participant DB as PostgreSQL

    U->>B: Click "Log out"
    B->>A: POST /api/auth/logout/
    A->>DB: DELETE PromptRun WHERE session_key = current_session
    DB-->>A: (cascades to ModelResponse rows)
    A->>DB: Destroy Session
    A-->>B: 204 No Content
    B->>B: Clear local state, navigate to Login screen
```

---

## 3. Load "New run" setup screen

Fires when the user opens the setup screen (after login, or via "New run" nav link). Populates
provider/model options, the system-prompt library, and the configured max prompt length.

```mermaid
sequenceDiagram
    actor U as User
    participant B as Browser
    participant A as API
    participant DB as PostgreSQL

    U->>B: Navigate to "New run"
    par
        B->>A: GET /api/providers/
        A-->>B: 200 {providers: [{name, models: [...]}]}
    and
        B->>A: GET /api/system-prompts/
        A->>DB: SELECT * FROM system_prompt ORDER BY name
        DB-->>A: rows
        A-->>B: 200 {results: [{id, name, text}]}
    and
        B->>A: GET /api/settings/
        A->>DB: SELECT * FROM app_settings LIMIT 1
        DB-->>A: {max_prompt_length}
        A-->>B: 200 {max_prompt_length}
    end
    B->>B: Render provider/model selectors, prompt textarea, char counter
```

---

## 4. Start a prompt run (fan-out)

The core flow: user submits a prompt N times (2–5). The API creates the run + N response rows
synchronously, then enqueues one Django-Q2 task per response, and returns immediately so the
frontend can start polling.

```mermaid
sequenceDiagram
    actor U as User
    participant B as Browser
    participant A as API
    participant DB as PostgreSQL
    participant Q as Broker (Redis)

    U->>B: Click "Run prompt N times"
    B->>B: Validate prompt length <= maxLen (client-side guard)
    B->>A: POST /api/runs/ {provider, model, system_prompt, prompt, run_count}
    A->>A: Re-validate run_count in [2,5] and prompt length <= max_prompt_length
    alt validation fails
        A-->>B: 400 Bad Request {errors}
    else validation passes
        A->>DB: INSERT PromptRun (user, session_key, provider, model, system_prompt, prompt, run_count)
        A->>DB: INSERT ModelResponse x run_count (status=queued)
        DB-->>A: PromptRun id, ModelResponse ids
        loop for each ModelResponse
            A->>Q: enqueue async_task("generate_response", response_id)
        end
        A-->>B: 201 Created {run_id, responses: [{id, index, status: "queued"}]}
        B->>B: Navigate to Run screen, start polling GET /api/runs/{run_id}/
    end
```

---

## 5. Background worker generates one response

One Django-Q2 worker process per queued task. Runs independently per response, so one slow/failed
call doesn't block the others.

```mermaid
sequenceDiagram
    participant Q as Broker (Redis)
    participant W as Worker (Django-Q2)
    participant DB as PostgreSQL
    participant LC as LangChain
    participant LLM as LLM Provider (OpenAI/Anthropic)

    Q->>W: Deliver task generate_response(response_id)
    W->>DB: UPDATE ModelResponse SET status='running', started_at=now()
    W->>DB: SELECT PromptRun (system_prompt, prompt, provider, model)
    DB-->>W: run details
    W->>LC: invoke(system_prompt, prompt, provider, model)
    LC->>LLM: Chat completion request (server-side API key from env)
    alt provider call succeeds
        LLM-->>LC: response text
        LC-->>W: response text
        W->>DB: UPDATE ModelResponse SET status='complete', response_text=..., completed_at=now()
    else provider call fails (timeout, 429, 5xx)
        LLM-->>LC: error
        LC-->>W: error
        W->>DB: UPDATE ModelResponse SET status='failed', error_message=..., retry_count+=1
        Note over W,DB: Non-fatal errors are auto-retried up to a configured max<br/>via Django-Q2's retry mechanism before being left as "failed"
    end
```

---

## 6. Poll run status (with diff)

The Run screen polls periodically (e.g. every 1.5–2s) until all responses reach a terminal state
(`complete` or `failed`). The API computes diff tokens for each non-baseline response against
`Run 1` (the baseline) once both are complete, so the frontend only has to toggle visibility.

```mermaid
sequenceDiagram
    actor U as User
    participant B as Browser
    participant A as API
    participant DB as PostgreSQL

    loop every ~2s while any response is queued/running
        B->>A: GET /api/runs/{run_id}/
        A->>DB: SELECT PromptRun + ModelResponse rows WHERE run_id=...
        DB-->>A: rows
        A->>A: For each complete non-baseline response,<br/>compute diff_tokens vs baseline response text
        A-->>B: 200 {run_id, status, responses: [{id, index, status, response_text, diff_tokens, error_message}]}
        B->>B: Update cards (queued/running shimmer, complete text, failed + retry button)
    end
    B->>U: Stop polling once every response is complete or failed
    U->>B: Toggle "Diff highlighting" On/Off
    B->>B: Re-render using cached diff_tokens (no API call)
```

---

## 7. Retry a failed response

```mermaid
sequenceDiagram
    actor U as User
    participant B as Browser
    participant A as API
    participant DB as PostgreSQL
    participant Q as Broker (Redis)

    U->>B: Click "Retry" on a failed response card
    B->>A: POST /api/responses/{response_id}/retry/
    A->>DB: SELECT ModelResponse WHERE id=response_id AND status='failed'
    alt response not found or not owned by user
        A-->>B: 404 Not Found
    else eligible for retry
        A->>DB: UPDATE ModelResponse SET status='queued', error_message=NULL
        A->>Q: enqueue async_task("generate_response", response_id)
        A-->>B: 202 Accepted {id, status: "queued"}
        B->>B: Card switches to "Retrying" state; resume polling
    end
```

---

## 8. Update app settings (max prompt length)

Settings screen, "Prompt limits" section.

```mermaid
sequenceDiagram
    actor U as User
    participant B as Browser
    participant A as API
    participant DB as PostgreSQL

    U->>B: Change "Maximum prompt length" and blur field
    B->>A: PATCH /api/settings/ {max_prompt_length}
    A->>A: Check requesting user is staff/admin
    alt not authorized
        A-->>B: 403 Forbidden
    else authorized
        A->>A: Validate 100 <= value <= 4000
        alt invalid value
            A-->>B: 400 Bad Request {errors}
        else valid
            A->>DB: UPDATE app_settings SET max_prompt_length=...
            A-->>B: 200 OK {max_prompt_length}
            B->>B: Update local maxLen used by the setup screen's char counter
        end
    end
```
