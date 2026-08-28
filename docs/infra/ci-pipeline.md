# CI Pipeline

The living record for [`LLMC-CORE-003`](../tasks/tasks/LLMC-CORE-003.md): how to run each
suite, what CI actually runs, and how to reproduce a red CI job on your machine. The
contracts it implements are [`testing.md`](./testing.md) and [`ci.md`](./ci.md); the stack it
runs against is [`stack-runbook.md`](./stack-runbook.md) and
[`../frontend/app-shell.md`](../frontend/app-shell.md).

At this stage the suites contain exactly the **two skeleton smoke tests** — one per half.
There are no feature tests yet, and that is the point: every later task can now write its
acceptance criteria as tests instead of as manual inspection.

## Running things

| Command | What it does |
|---|---|
| `make test` | Everything, exactly as CI runs it → `scripts/ci-test.sh` |
| `make test-backend` | `ruff check .` + `pytest --cov` in the `backend` container |
| `make test-frontend` | `npm run lint` + `vitest --run` in the `frontend` container |
| `make lint` | Both linters, no tests |
| `make fmt` | `ruff format` + `prettier --write`, in place |

`scripts/ci-test.sh` is the single definition of "the suite". The Makefile targets pass it
`--backend` / `--frontend` rather than repeating the commands, so there is one place where a
command can change and no way for the halves to drift apart.

**Formatting is not a gate.** `make lint` is ruff + eslint only; Prettier and `ruff format`
are available through `make fmt` but nothing fails a build over whitespace. ESLint carries no
stylistic rules for the same reason — the two tools can never disagree about the same line.

`frontend/.prettierignore` excludes `src/styles/`. Those files are a verbatim transcription of
`docs/frontend/mock/styles.css` (see [`app-shell.md`](../frontend/app-shell.md)); reformatting
them would turn the next reskin from a file copy into a diff against a moving target.

## The backend suite

Configuration lives in `backend/pytest.ini`, ruff's in `backend/pyproject.toml`. Two things
there are worth knowing.

**`--ds=config.settings.test` is in `addopts`, not `DJANGO_SETTINGS_MODULE` in the ini.** Every
container built from the backend image already has `DJANGO_SETTINGS_MODULE=config.settings.local`
in its environment (`docker-compose.yml`), and pytest-django ranks the **environment above the
ini key** — so the ini key loses silently and the suite runs against dev settings, with async
Django-Q2 and the real password hashers, while still looking correct. `--ds` is a command-line
option and outranks both. This was observed, not predicted: the first green run reported
`settings: config.settings.local (from env)` in its own header.

**`testpaths = .`**, not a list of app names. Tests live in per-app `tests/` packages, and a new
app should not need a config edit before its tests run.

`config/settings/test.py` is Postgres-backed on purpose — pytest-django creates and drops
`test_<POSTGRES_DB>` on the same `db` service, so the dev database is never touched but the
column types and constraints under test are the real ones. It also sets `Q_CLUSTER["sync"] =
True` (enqueued tasks run inline, so no `worker` container is needed), the MD5 password hasher,
and a hardcoded non-secret `SECRET_KEY`.

Shared fixtures are in `backend/core/tests/conftest.py`:

- `api_client` is a **factory**, not a client. Ownership tests in `LLMC-RUNS-*` need two
  independently logged-in clients inside one test, which a single shared instance cannot
  express.
- `app_settings` returns `AppSettings.load()` rather than a `factory_boy` factory. The model
  pins `pk = 1` on save, so "make another one" is not a thing a test can do, and a factory would
  only hide that.

### The health smoke test asserts the exact key set

`core/tests/test_health.py` compares `set(payload)` to the four keys with `==`, not with a
subset check. A subset check still passes after a key is *renamed*, which is precisely the
regression worth catching: the same payload is the Compose healthcheck for the `backend`
service and the landing page's only real data.

The test lets the health view ping **real** Redis rather than mocking it. That is deliberate:
the endpoint's whole reason for existing is that it cannot pass without touching Postgres and
Redis ([`stack-runbook.md`](./stack-runbook.md)), so a mocked broker would test a different
endpoint than the one Compose relies on. It is why `ci-test.sh` runs `docker compose up -d db
broker` first, and why the CI job keeps a `redis` service container even though nothing enqueues
a task.

Adding `requirements/dev.txt` also split `backend/Dockerfile` into a `runtime` stage and a `dev`
stage. `dev` is deliberately **last**, so a plain `docker compose build` produces the image the
test targets need; the split exists so that a future `--target runtime` build genuinely lacks
pytest and ruff, rather than a comment promising nobody installed them.

## The frontend suite

Vitest in a jsdom environment, React Testing Library, and msw for the network.
`frontend/vitest.config.ts` **merges the app's own `vite.config.ts`** instead of restating it —
a test that passed against a differently-configured build would be testing something the app
never runs.

`src/test/setup.ts` starts the msw server with `onUnhandledRequest: "error"`. That single option
is what makes the suite honest: any fetch a component makes that no handler covers fails the
test loudly instead of escaping to the real network and quietly making the suite depend on a
running backend. Handlers in `src/test/handlers.ts` are keyed off `API_BASE_URL` rather than a
hardcoded string, so changing the base URL moves the mocks with the client.

**`frontend/.env.test` is load-bearing, not decoration.** `api/client.ts` reads
`import.meta.env.VITE_API_BASE_URL` at module scope and would throw on `undefined`, so without
that file the API client is not even importable under Vitest. Vitest runs in mode `test`, which
is what makes Vite load it.

`src/layouts/AppShell.test.tsx` renders `<Landing />` inside a `MemoryRouter`, **not** `<App />`:
`App` owns a `BrowserRouter` and nesting routers throws. It asserts the nav renders, that the
mocked `max_prompt_length` of `600` reaches the screen, that the active link is marked with
`aria-current` (the same attribute the CSS keys off, per
[`app-shell.md`](../frontend/app-shell.md)), and that a 503 renders the error state.

`npm test` is `vitest --run`, with watch mode moved to `npm run test:watch`. The default has to
be non-interactive — a watch-mode default hangs `make test-frontend` and every CI job forever.

## What CI runs

`.github/workflows/ci.yml`, on pull requests to `main` and pushes to `main`. Three jobs, no
`needs:` between them, so all three run in parallel:

| Job | Steps |
|---|---|
| `backend-test` | `postgres:16-alpine` + `redis:7-alpine` service containers → `pip install -r backend/requirements/dev.txt` (pip cache keyed on that file) → `ruff check .` → `pytest --cov --cov-report=term-missing` |
| `frontend-test` | `npm ci` (npm cache keyed on `frontend/package-lock.json`) → `npm run lint` → `npm test -- --run` |
| `docker-build` | `docker compose build` — catches drift between `requirements/`/`package.json` and the images. Builds only; the stack is never started. |

**The jobs run natively, not through Compose**, while `scripts/ci-test.sh` runs the same four
commands *through* Compose. That is the one intentional difference between local and CI: the
runner gets warm pip/npm caches and skips the image build, while a developer gets the exact
image the stack uses. The commands themselves are identical, which is the part that matters —
`docker-build` covers the images CI would otherwise never exercise.

**No secrets, and this is enforced rather than hoped for.** `OPENAI_API_KEY` and
`ANTHROPIC_API_KEY` are set to `""` in the job env, so a test that reached for a real key fails
CI rather than passing on a laptop that happens to have one. `SECRET_KEY` is hardcoded in
`config/settings/test.py`. The task's verification greps the workflow for `secrets.` and fails
if any appears, so a future job that quietly needs one is caught at the task level.

`concurrency: cancel-in-progress` means a new push to a PR supersedes the run in flight.

**Branch protection is not in this file.** Requiring `backend-test`, `frontend-test` and
`docker-build` before merging to `main` is a repository setting; it is noted in
[`ci.md`](./ci.md) so it is not lost.

## Reproducing a CI failure locally

```bash
bash scripts/ci-test.sh                 # both halves, the way CI runs them
bash scripts/ci-test.sh --backend       # or just one
docker compose build                    # what docker-build does
```

If the local run is green and CI is red, the difference is almost always one of:

| Symptom | Cause |
|---|---|
| Backend passes locally, fails in CI | A stale local image. CI installs from `requirements/dev.txt` every run; `docker compose build backend` locally. |
| `npm ci` fails in CI only | `package.json` changed without `package-lock.json`. Run `docker compose run --rm frontend npm install --package-lock-only` and commit the lock. |
| Backend fails on the DB | `db` is not up. `ci-test.sh` starts it; a bare `docker compose run --rm backend pytest` does not wait for health. |
| `pytest` picks the wrong settings | The header line does not say `(from option)` — something removed `--ds` from `pytest.ini`'s `addopts`. |
| Vitest hangs | `npm test` was pointed back at watch mode. |

## Deliberately not here

Coverage thresholds (`--cov` reports, nothing gates on the number — revisit at `LLMC-REL-001`
if coverage becomes a release criterion), end-to-end browser tests (out of scope per
[`testing.md`](./testing.md)), and any deploy job — the hosting target is local only.
