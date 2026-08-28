---
id: LLMC-CFG-001
title: Providers, app settings and system-prompt library API
area: CFG
phase: 2
layer: backend
status: todo
review: none
depends_on:
  - LLMC-AUTH-002
docs:
  read:
    - docs/backend/api-endpoints.md
    - docs/backend/db-schema.md
    - docs/backend/auth-contract.md
    - docs/infra/environment.md
  write:
    - docs/backend/config-backend.md
---

# LLMC-CFG-001 - Providers, app settings and system-prompt library API

## Objective

After this task the API serves everything the Setup and Settings screens need before a run can be
configured: the provider/model catalog, the shared prompt-length limit (readable by anyone, writable
only by staff), and the saved system-prompt library. These are the three parallel calls in diagram 3
of `docs/backend/sequence-diagrams.md`.

## Scope

**In:**

- `settings.LLM_PROVIDERS`: the static, env-driven provider/model catalog from
  `docs/backend/api-endpoints.md` (OpenAI and Anthropic with their model lists), plus
  `GET /api/providers/` serving it and a helper `is_valid_pair(provider, model)` that
  `LLMC-RUNS-001` will reuse for validation.
- `GET /api/settings/` and `PATCH /api/settings/` over the existing `AppSettings` singleton: staff-only
  write, `[100, 4000]` validation, `{error, detail}` on failure.
- `prompts.SystemPrompt` model from `docs/backend/db-schema.md` + migration, a data migration seeding
  the two default prompts shown in `docs/backend/api-endpoints.md`, `GET /api/system-prompts/` ordered
  by name, and Django admin registration for `SystemPrompt` and `AppSettings`.
- `prompts/tests/` covering the permission matrix, validation bounds and ordering.

**Out:**

- Create/update/delete endpoints for `SystemPrompt` — the API contract exposes read only; the library is
  curated by an admin through Django admin. Recorded as a scope decision in the living doc.
- Per-user prompt libraries or favourites (nothing in the spec asks for ownership semantics beyond the
  optional `created_by` column).
- Any provider connectivity or key-validity check; `GET /api/providers/` is a static catalog and must
  never touch the network or read API keys.
- Runtime editing of the provider catalog (env + restart only) and any UI (`LLMC-CFG-002`).

## Outputs

- `backend/config/settings/base.py`: `LLM_PROVIDERS`
- `backend/prompts/{models,serializers,views,urls,admin}.py`, `SystemPrompt` migration + seed migration
- Endpoints: `GET /api/providers/`, `GET /api/settings/`, `PATCH /api/settings/`,
  `GET /api/system-prompts/`
- `backend/prompts/tests/{test_settings_api.py,test_system_prompts.py,test_providers.py}`
- `docs/backend/config-backend.md` — shipped behaviour, the catalog's shape and how to extend it, and
  the read-only-library decision

## Acceptance criteria

- [ ] `GET /api/providers/` returns `200` with both `OpenAI` and `Anthropic`, each with a non-empty
      `models` list, and the payload contains no key-like value.
- [ ] All four endpoints return `401` without a session.
- [ ] `GET /api/settings/` returns the current `max_prompt_length` from the singleton row.
- [ ] `PATCH /api/settings/` as a non-staff user returns `403` and leaves the stored value unchanged.
- [ ] `PATCH /api/settings/` as staff with `850` returns `200`, and the next `GET /api/settings/` and
      `GET /api/health/` both report `850`.
- [ ] `PATCH /api/settings/` with `50` and with `5000` both return `400` with an `{error, detail}` body.
- [ ] `GET /api/system-prompts/` returns the seeded prompts ordered by `name`, each with `id`, `name`
      and `text`.
- [ ] Re-running the seed migration on a database that already has the defaults does not duplicate them.
- [ ] `pytest prompts` passes and `manage.py migrate --check` exits `0`.

## Verification

```bash
cd "$(git rev-parse --show-toplevel)"
docker compose up -d db broker backend
docker compose run --rm backend pytest prompts -q
docker compose run --rm backend python manage.py migrate --check
docker compose run --rm backend python manage.py shell -c \
  "from prompts.models import SystemPrompt as S; assert S.objects.count() == S.objects.values('name').distinct().count()"
for p in providers settings system-prompts; do \
  curl -s -o /dev/null -w '%{http_code}\n' "http://localhost:8000/api/$p/" | grep -q 401; done
```

## Evidence

_None recorded yet._
