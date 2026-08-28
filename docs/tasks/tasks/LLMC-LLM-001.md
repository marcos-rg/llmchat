---
id: LLMC-LLM-001
title: LLM orchestration and worker task contract
area: LLM
phase: 3
layer: contract
status: todo
review: none
depends_on:
  - LLMC-CORE-001
docs:
  read:
    - docs/specs/specs.md
    - docs/backend/sequence-diagrams.md
    - docs/backend/db-schema.md
    - docs/infra/architecture.md
    - docs/infra/environment.md
    - docs/infra/testing.md
  write:
    - docs/backend/llm-contract.md
---

# LLMC-LLM-001 - LLM orchestration and worker task contract

## Objective

After this task there is a reviewed decision for the one part of the system the existing docs leave
under-specified: the seam between the queue and the provider SDKs. It fixes the adapter signature, the
worker task's exact status transitions and DB writes, which failures retry and which do not, how API
keys are kept out of logs, the patch point tests mock, and the offline fake provider that lets the
whole stack be exercised without real keys or credit spend.

## Scope

**In:** `docs/backend/llm-contract.md` covering:

- Adapter interface: `llm.client.generate(provider, model, system_prompt, prompt, *, timeout) -> str`,
  the provider-to-LangChain-class mapping, and which environment variable each provider reads.
- A typed error taxonomy (`ProviderAuthError`, `ProviderRateLimited`, `ProviderTimeout`,
  `ProviderUnavailable`, `ProviderBadRequest`, `ProviderNotConfigured`) with, for each, whether it is
  retryable and what `error_message` the user sees — user-facing text must never include the key,
  the raw request or a stack trace.
- Worker task `runs.tasks.generate_response(response_id)`: the exact dotted path
  `LLMC-RUNS-001` enqueues, its status transitions across all five `ModelResponse.Status` values from
  `docs/backend/db-schema.md`, which fields it writes (`started_at`, `completed_at`, `response_text`,
  `error_message`, `retry_count`), and its behaviour when the row is already terminal or already
  running (idempotency under duplicate delivery).
- Retry policy: `settings.LLM_MAX_ATTEMPTS` (default 2) plus per-attempt timeout, the relationship
  Django-Q2 requires between `Q_CLUSTER["timeout"]` and `Q_CLUSTER["retry"]`, and how the automatic
  attempts relate to the user-driven `POST /api/responses/{id}/retry/` (which resets state and
  re-enqueues rather than resuming).
- Logging rules: which fields may be logged, and the masking helper that guarantees a key value never
  reaches a log record even inside an SDK exception message.
- The offline fake provider: `LLM_FAKE_PROVIDER=1` routes every call to a deterministic local adapter
  that returns near-identical text with small controlled variation (so the diff view has something to
  show), induces a failure when the prompt begins with `FAIL:`, and honours a configurable delay. This
  is the mechanism all stack-level verification and load checks use.
- The single patch point that `docs/infra/testing.md` requires unit tests to mock.

**Out:**

- Implementation of any of the above (`LLMC-LLM-002`), the run models and endpoints
  (`LLMC-RUNS-001`), and diffing (`LLMC-DIFF-001`).
- Streaming responses, token/cost accounting, LangGraph multi-step graphs, model fallback chains and
  per-user keys — none are in `docs/specs/specs.md`.
- Prompt templating beyond passing the system prompt and user prompt straight through.

## Outputs

- `docs/backend/llm-contract.md`
- Amendments to `docs/infra/environment.md` for `LLM_FAKE_PROVIDER`, `LLM_TIMEOUT_SECONDS` and
  `LLM_MAX_ATTEMPTS`, with their container ownership

## Acceptance criteria

- [ ] The contract names the adapter function with its full signature and return type, and states the
      environment variable each provider reads.
- [ ] It contains a transitions table covering all five statuses from `docs/backend/db-schema.md`
      (`queued`, `running`, `retrying`, `complete`, `failed`) and, for each transition, which component
      writes it.
- [ ] Every error class in the taxonomy is listed with an explicit retryable yes/no and its user-facing
      message.
- [ ] It names the exact dotted task path and argument list that the run API will enqueue, and states
      the behaviour on duplicate delivery of the same task.
- [ ] It names the single patch point unit tests mock, and states that no test may make a network call.
- [ ] The fake provider section documents its env flag, its failure trigger and its delay control.
- [ ] `docs/infra/environment.md` documents all three new variables and which containers receive them.
- [ ] Every relative markdown link in the contract resolves.

## Verification

```bash
cd "$(git rev-parse --show-toplevel)"
C=docs/backend/llm-contract.md
test -f "$C"
grep -q 'def generate' "$C"
for s in queued running retrying complete failed; do grep -q "$s" "$C"; done
for e in ProviderAuthError ProviderRateLimited ProviderTimeout ProviderUnavailable \
         ProviderBadRequest ProviderNotConfigured; do grep -q "$e" "$C"; done
grep -q 'runs.tasks.generate_response' "$C"
grep -qi 'idempot' "$C"
grep -q 'LLM_FAKE_PROVIDER' "$C"
grep -q 'FAIL:' "$C"
grep -qi 'mask' "$C"
grep -q 'LLM_MAX_ATTEMPTS' "$C"
for v in LLM_FAKE_PROVIDER LLM_TIMEOUT_SECONDS LLM_MAX_ATTEMPTS; do \
  grep -q "$v" docs/infra/environment.md; done
grep -o '](\.\./[^)#]*\|](\./[^)#]*' "$C" | sed 's/^](//' | while read -r l; do \
  test -e "docs/backend/$l" || { echo "broken link: $l"; exit 1; }; done
```

## Evidence

_None recorded yet._
