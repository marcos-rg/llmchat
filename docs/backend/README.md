# Backend Design

This folder documents the backend design derived from [`docs/specs/specs.md`](../specs/specs.md)
and the UI mockups in [`docs/UI/`](../UI/). It is split into three documents that should be read
in order:

1. [`sequence-diagrams.md`](./sequence-diagrams.md) — every user-triggered action, shown as a
   sequence diagram across Browser (React) → Django API → Django-Q2 worker → Redis → LangChain →
   LLM provider → PostgreSQL.
2. [`api-endpoints.md`](./api-endpoints.md) — one section per endpoint referenced by the diagrams:
   method, auth, request/response payloads, status codes, and error cases.
3. [`db-schema.md`](./db-schema.md) — the Django ORM models backing those endpoints, plus notes on
   how the "ephemeral data" requirement is enforced at the DB level.

## Component map

| Component | Responsibility |
|---|---|
| **Browser (React)** | Renders the screens in `docs/UI/`; polls for run status; computed diff toggle is purely client-side rendering. |
| **Django API** | Auth, request validation, run/response CRUD, enqueues background jobs. |
| **Redis** | Message broker for Django-Q2. |
| **Django-Q2 worker** | Executes one LLM call per queued task; updates response status in PostgreSQL. |
| **LangChain / LangGraph** | Thin orchestration layer the worker calls to talk to OpenAI/Anthropic with a uniform interface. |
| **PostgreSQL** | Stores users, the system-prompt library, app settings, and the *active-session* prompt runs/responses. |
