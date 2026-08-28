# Project types

The **single definition** of the four project types and what each one changes. `docs/specs/specs.md`
declares which type this project is under `## Project Type`. Every agent — spec reviewer, task
generator, task executor — reads that declaration and applies the column below. No agent may restate
or redefine these profiles; if a profile needs to change, it changes here.

If `specs.md` declares no type, treat the project as **MVP** and say so explicitly in your report.
Do not silently pick a type, and do not infer one from the stack or the repository's polish.

## What each type is

| Type | Goal | Lifespan | Success is |
|---|---|---|---|
| `hackathon` | Show the idea working, live, under time pressure | Days. Thrown away or rewritten after. | The demo path runs end to end without a babysitter |
| `poc` | Answer one technical question with evidence | Weeks. The answer outlives the code. | The question is answered and the answer is written down |
| `mvp` | Put the smallest real thing in front of real users | Months. Will be extended, by others. | Users complete the core job; the team can keep building on it |
| `production` | Run a service people depend on | Years. Operated, on-call, audited. | It stays correct and available under failure, load, and attack |

**Priority order** — when two goals conflict, the earlier one wins:

- `hackathon` — **working demo path** > speed > everything else. Fast but broken is a failure, not a tradeoff.
- `poc` — **validity of the answer** > speed > reusability. A fast answer you cannot trust is worthless.
- `mvp` — **user-visible correctness** > iterability > completeness > polish.
- `production` — **robustness** (correctness, security, recoverability, observability) > completeness > speed.

## The profile matrix

| Dimension | `hackathon` | `poc` | `mvp` | `production` |
|---|---|---|---|---|
| **Phase 0 skeleton** | Minimal: one page → one endpoint → one row, nothing more | Minimal, plus whatever instrumentation the question needs measured | Full walking skeleton: config, error envelope, migrations, CI | Full skeleton plus CI gates, secret handling, structured logging, health checks |
| **Task sizing** | Half a day; prefer fewer, wider slices | Half a day; the experiment is one slice | ~One day, one PR, one reviewable increment | ~One day; split anything that mixes a behavior change with an operational one |
| **Total task count** | As few as reach the demo | As few as reach the answer | Whatever the user-facing scope needs | Scope plus an explicit hardening phase |
| **Tests** | Happy path of the demo path only | Only what makes the measurement trustworthy | Unit tests on business logic + one E2E per feature slice | Unit + integration + E2E + failure-mode tests (timeouts, retries, partial failure) |
| **Error handling** | Fail visibly, never silently; no recovery required | Same, plus record failures that would skew the result | Every user-facing error has a defined message and state | Every error has a defined class, retry/backoff policy, and operator-visible signal |
| **Security** | Do not leak secrets to the client or logs. That is the whole bar. | Same | Authn/authz enforced on every protected path; input validated at the boundary | Full posture: threat model, least privilege, rate limits, dependency and secret scanning, audit trail |
| **Observability** | Console logs are fine | Whatever the measurement needs | Structured logs on errors and job lifecycle | Structured logs, metrics, traces, alerting on the stated SLO |
| **Performance** | Must not stall the demo | Measured, because it is usually the question | Meet the stated concurrent-user target | Load-tested against a stated target with headroom |
| **Living docs (`docs.write`)** | A short "how to run and demo it" note | The experiment: method, data, result, conclusion | Contract + decisions + how to extend it | The above plus runbook, failure modes, rollback |
| **`contract` tasks** | Skip unless two slices must agree on a shape | Skip unless the contract *is* the question | For any non-obvious cross-layer design | For every cross-layer or externally consumed interface |
| **Review gates (`review: human`)** | At most one: the demo itself | One: the conclusion | A small handful: architecture, security posture, UX sign-off | The MVP set plus release, plus any change to the security or data model |
| **Hardening phase** | None | None | Light: security pass, perf against target, acceptance | Full: security, performance, DR/rollback, packaging, release |
| **Definition of done** | The demo path runs on the real stack | The result is reproducible and written down | Criteria pass and the feature works for a real user | Criteria pass under failure and load, and the change is operable and reversible |

## Applying it

**Cutting scope is the point, and it has a floor.** A cheaper type removes *work*, never *truth*.
Every type keeps: acceptance criteria that are checkable by running something, verification that
actually ran, evidence recorded, and no secret in a client or a log. `hackathon` means fewer tests,
not unrun ones; it never means a criterion marked done that was not checked.

**The type is a floor, not a ceiling, on judgment.** If a `hackathon` project handles real user data,
or a `poc` calls a paid API in a loop, apply the stricter bar for that specific concern and say why
in your report.

**Escalation is a human decision.** A project's type changes only when a human edits `specs.md`.
Never upgrade a project's type because the code looks like it deserves one, and never quietly build
to a stricter bar than declared — over-building on a `hackathon` clock is the same failure as
under-building on a `production` one.
