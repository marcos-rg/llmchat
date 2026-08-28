# Continuous Integration

GitHub Actions, one workflow at `.github/workflows/ci.yml`. Goal: catch lint/test failures on every
PR without needing real infrastructure or secrets — everything the pipeline needs either runs as a
GitHub Actions service container or is mocked (see [`testing.md`](./testing.md)).

## Triggers

```yaml
on:
  pull_request:
    branches: [main]
  push:
    branches: [main]
```

## Jobs

| Job | Runs on | Steps |
|---|---|---|
| `backend-test` | `ubuntu-latest`, with `postgres` and `redis` service containers | Install deps from `backend/requirements/dev.txt` → `ruff check` → `pytest --cov` against the service-container Postgres (Django-Q2 set to sync mode, same as local — no `redis` traffic actually needed by tests, but the service container is cheap and keeps parity with `docker-compose.yml`) |
| `frontend-test` | `ubuntu-latest` | `npm ci` in `frontend/` → `npm run lint` → `npm test -- --run` |
| `docker-build` | `ubuntu-latest` | `docker compose build` — verifies both Dockerfiles still build; catches drift between `requirements/`/`package.json` and the images before merge. Does not run the stack or tests. |

`backend-test` and `frontend-test` run in parallel (independent jobs, no `needs:`); `docker-build` can
also run in parallel since it only needs the Dockerfiles/build context, not test results.

## Service containers (`backend-test` job)

```yaml
services:
  postgres:
    image: postgres:16-alpine
    env:
      POSTGRES_DB: llmchat_test
      POSTGRES_USER: llmchat
      POSTGRES_PASSWORD: llmchat
    ports: ["5432:5432"]
    options: >-
      --health-cmd pg_isready
      --health-interval 5s
      --health-timeout 5s
      --health-retries 10
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    options: >-
      --health-cmd "redis-cli ping"
      --health-interval 5s
      --health-timeout 5s
      --health-retries 10
```

GitHub Actions waits on the healthchecks automatically before starting later steps in the job.

## Secrets required

**None.** By design:

- `OPENAI_API_KEY`/`ANTHROPIC_API_KEY` are never read in tests — the `llm` app's tests mock the
  LangChain provider clients (see [`testing.md`](./testing.md)). CI sets these to empty strings (or
  omits them) in the job's `env:`.
- `DJANGO_SECRET_KEY` for the `test` settings module can be a hardcoded non-secret value
  (`config/settings/test.py`), since it never faces real traffic.
- No deployment step exists (local-only hosting target, per `docs/specs/specs.md`), so no cloud
  credentials are needed either.

If a deploy target is added later, deployment credentials would be added as repo/environment secrets
at that point — out of scope for the current spec.

## Caching

- `frontend-test`: cache `~/.npm` keyed on `frontend/package-lock.json` (`actions/setup-node`'s
  built-in `cache: npm` with `cache-dependency-path: frontend/package-lock.json`).
- `backend-test`: cache `~/.cache/pip` keyed on `backend/requirements/dev.txt`
  (`actions/setup-python`'s built-in `cache: pip`).
- `docker-build`: optionally use `docker/build-push-action` with GitHub Actions cache
  (`cache-from`/`cache-to: type=gha`) if build times become a problem; not needed at current scope.

## Branch protection (recommended, configured in repo settings, not in this workflow file)

Require `backend-test`, `frontend-test`, and `docker-build` to pass before merging to `main`. Not
part of the YAML itself — noted here so it isn't lost as a manual setup step.
