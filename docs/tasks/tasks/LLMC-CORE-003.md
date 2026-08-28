---
id: LLMC-CORE-003
title: Test harness, linting and CI pipeline
area: CORE
phase: 0
layer: infra
status: done
issue: https://github.com/marcos-rg/llmchat/issues/8
review: none
depends_on:
  - LLMC-CORE-001
  - LLMC-CORE-002
docs:
  read:
    - docs/infra/testing.md
    - docs/infra/ci.md
    - docs/infra/stack-runbook.md
    - docs/frontend/app-shell.md
  write:
    - docs/infra/ci-pipeline.md
---

# LLMC-CORE-003 - Test harness, linting and CI pipeline

## Objective

After this task both halves of the skeleton are guarded: `make test` and `make lint` run backend and
frontend suites the same way CI does, and `.github/workflows/ci.yml` runs them on every pull request
with no secrets. Every later task can therefore state its acceptance criteria as tests instead of
manual inspection.

## Scope

**In:**

- `backend/requirements/dev.txt` (base + `pytest`, `pytest-django`, `pytest-cov`, `factory_boy`,
  `ruff`, `PyYAML`), installed into the backend image's dev stage.
- `backend/config/settings/test.py` per `docs/infra/testing.md`: the Django-managed
  `test_<POSTGRES_DB>` on the same Postgres service, `Q_CLUSTER["sync"] = True`, MD5 password hasher,
  hardcoded non-secret `SECRET_KEY`.
- `pytest.ini`/`pyproject.toml` config (`DJANGO_SETTINGS_MODULE=config.settings.test`, test paths),
  `ruff` config, and `backend/core/tests/` shared fixtures (API client factory, `AppSettings` fixture).
- Backend smoke test asserting `GET /api/health/` returns `200` with all four payload keys.
- Frontend: `vitest` + `@testing-library/react` + `jsdom` + `msw` handlers directory, `eslint` and
  `prettier` configs, `npm test`/`npm run lint` scripts, and a shell test asserting the landing route
  renders `max_prompt_length` from an msw-mocked `/health/`.
- `scripts/ci-test.sh` (exact commands from `docs/infra/testing.md`) and Makefile `test`,
  `test-backend`, `test-frontend`, `lint`, `fmt` targets delegating to it.
- `.github/workflows/ci.yml`: `backend-test` (postgres + redis service containers, pip cache, ruff,
  pytest --cov), `frontend-test` (npm cache, eslint, vitest --run), `docker-build`
  (`docker compose build`), all three parallel, triggered on PRs to and pushes to `main`.

**Out:**

- Any feature tests — the only tests here are the two skeleton smoke tests.
- Coverage thresholds/gates (revisit at `LLMC-REL-001` if coverage becomes a release criterion).
- End-to-end browser tests (Playwright/Cypress) — explicitly out of scope per `docs/infra/testing.md`.
- Branch-protection settings, which live in repo settings, not in the workflow file.
- Any CI deploy job; the hosting target is local only.

## Outputs

- `backend/requirements/dev.txt`, `backend/config/settings/test.py`, `pytest.ini`, ruff config
- `backend/core/tests/{conftest.py,test_health.py}`
- `frontend/vitest.config.ts`, `frontend/src/test/setup.ts`, `frontend/src/test/handlers.ts`,
  `frontend/src/layouts/AppShell.test.tsx`, eslint/prettier configs
- `scripts/ci-test.sh`, `.github/workflows/ci.yml`, Makefile test/lint/fmt targets
- `docs/infra/ci-pipeline.md` — how to run each suite, what CI runs, and how to reproduce a CI failure
  locally.

## Acceptance criteria

- [ ] `make test-backend` runs pytest against `config.settings.test` and passes, including the health
      smoke test; the smoke test fails if a key is removed from the health payload.
- [ ] Backend tests pass with `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` set to empty strings.
- [ ] `make test-frontend` passes, including the shell test that asserts the landing route renders the
      mocked `max_prompt_length` (`600`) with no real network call.
- [ ] `make lint` exits `0` (ruff on `backend/`, eslint on `frontend/`) and fails on a deliberately
      introduced violation.
- [ ] `scripts/ci-test.sh` exits `0` and runs the same four commands CI runs.
- [ ] `.github/workflows/ci.yml` parses as YAML and defines exactly the jobs `backend-test`,
      `frontend-test` and `docker-build`, with no `secrets.` reference anywhere in the file.
- [ ] The workflow reports success on this task's pull request.

## Verification

```bash
cd "$(git rev-parse --show-toplevel)"
docker compose up -d db broker
make lint
make test-backend
make test-frontend
docker compose run --rm -e OPENAI_API_KEY= -e ANTHROPIC_API_KEY= backend pytest -q
bash scripts/ci-test.sh
docker compose run --rm -v "$PWD/.github:/gh:ro" backend python -c \
  "import yaml; d=yaml.safe_load(open('/gh/workflows/ci.yml')); assert set(d['jobs']) == {'backend-test','frontend-test','docker-build'}, d['jobs']"
! grep -q 'secrets\.' .github/workflows/ci.yml
gh run list --branch "$(git rev-parse --abbrev-ref HEAD)" --limit 3 || echo "no gh CLI: record the PR check result in evidence"
```

## Evidence

- `2026-08-28 09:36` make test-backend -> ruff 'All checks passed!'; pytest 2 passed, header 'settings: config.settings.test (from option)', coverage TOTAL 92%

- `2026-08-28 09:36` Health smoke test is real: deleting the 'broker' key from core/views.py's payload -> '1 failed, 1 passed' (test_health_returns_ok_with_the_full_payload); reverted

- `2026-08-28 09:36` docker compose run --rm -e OPENAI_API_KEY= -e ANTHROPIC_API_KEY= backend pytest -q -> 2 passed

- `2026-08-28 09:36` make test-frontend -> vitest --run, 1 file / 3 tests passed (landing route renders mocked max_prompt_length 600; msw onUnhandledRequest:'error' so no real network call)

- `2026-08-28 09:36` make lint -> exit 0; exit 2 with a deliberate ruff violation (backend/core/_lintcanary.py) and again with a deliberate eslint violation (frontend/src/_lintcanary.ts); both canaries removed

- `2026-08-28 09:36` bash scripts/ci-test.sh -> exit 0 (ruff check, pytest --cov --cov-report=term-missing, npm run lint, npm test -- --run)

- `2026-08-28 09:36` yaml.safe_load('.github/workflows/ci.yml') -> jobs == {backend-test, frontend-test, docker-build}; 'grep -q secrets\.' finds nothing

- `2026-08-28 09:36` docker compose build -> llmchat-backend:local and llmchat-frontend:local both built

- `2026-08-28 09:36` python3 scripts/tasks.py verify LLMC-CORE-003 --run -> exit 0

- `2026-08-28 09:36` gh pr checks 9 -> Backend (ruff + pytest) pass, Frontend (eslint + vitest) pass, Docker images build pass (run 33180913842)
