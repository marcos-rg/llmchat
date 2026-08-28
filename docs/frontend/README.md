# Frontend Design

This folder documents the frontend's design source of truth, derived from the interactive mockup in
[`mock/`](./mock/) (`LLMChat Mockups.dc.html` + `styles.css` — open the `.dc.html` in a browser to
click through the four screens) and cross-referenced against
[`docs/backend/`](../backend/README.md) and [`docs/specs/specs.md`](../specs/specs.md). It's split into
six documents, meant to be read in order:

1. [`style-guide.md`](./style-guide.md) — design tokens: color, type, spacing, radius, elevation, and
   the "blueprint" visual skin applied on top of them.
2. [`components.md`](./components.md) — every reusable UI component (buttons, fields, cards, tags,
   nav, table, dialog, skeleton bars), its variants, and its states.
3. [`layouts.md`](./layouts.md) — the app shell, container patterns, and the Run screen's
   horizontal-scroll-with-sticky-baseline layout.
4. [`pages.md`](./pages.md) — the four screens (Login, Setup, Run, Settings), their fields/elements,
   and which backend endpoint each is wired to.
5. [`interfaces.md`](./interfaces.md) — API DTOs (mirroring `docs/backend/api-endpoints.md`) plus the
   frontend-only view models and component prop boundaries built on top of them.
6. [`states.md`](./states.md) — the per-response status machine (queued/running/retrying/failed/
   complete), the run-level polling contract, and the diff-toggle interaction.
7. [`animations.md`](./animations.md) — the spin/shimmer keyframes used for in-progress responses, and
   the `prefers-reduced-motion` handling still to be implemented.

## How this doc set is meant to evolve

The project is explicitly modular and incremental — each document above owns one concern and can be
extended independently as the frontend is built out (new components go in `components.md`, a new page
gets a new section in `pages.md`, etc.). When implementation diverges from the mock (which is a static
prototype, not the shipped code), **update these docs to match the real, shipped behavior** rather than
letting them drift — they're the reference for "how this UI is supposed to look and behave," not a
historical record of the mock.

## Known gaps (intentionally not modeled in the mock)

- No responsive/mobile breakpoints — desktop-first only (see `layouts.md`).
- No login failure state, no dialog/confirmation flows, no table usage yet (see `pages.md` / `states.md`).
- `DiffToken`'s exact wire shape isn't specified by the backend yet — `interfaces.md` documents the
  mock's working assumption to confirm against the real API.
