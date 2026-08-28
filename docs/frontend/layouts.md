# Layouts

Source of truth: the per-page wrapper markup in
[`mock/LLMChat Mockups.dc.html`](./mock/LLMChat%20Mockups.dc.html). This is a **desktop-first, single
breakpoint** mock — no `@media` queries exist in `styles.css` or the page markup. Treat responsive
behavior below `~900px` as an open gap to design when the project reaches that increment, not as an
implemented and hidden behavior.

## App shell

Two shells exist, chosen by auth state:

1. **Unauthenticated shell** (Login only): a single full-viewport flex container
   (`min-height:100vh; display:flex; align-items:center; justify-content:center`) centering one card.
2. **Authenticated shell** (Setup / Run / Settings): full-viewport flex column
   (`min-height:100vh; display:flex; flex-direction:column`) with:
   - a fixed-height `.nav` bar (bottom hairline border) — brand, "New run", "Settings", current
     user email (pushed right via the brand's `margin-right:auto`), "Log out"
   - a `<main>` that grows to fill remaining height (`flex:1`) and is swapped per-page

The nav's two links use `aria-current="page"` (via `setupCurrent`/`settingsCurrent`) to mark the active
page — carry this through to real routing (e.g. `NavLink`'s `aria-current` in React Router) rather than
a manual class.

## Content containers

Two container patterns are used depending on whether the page is form-like or data-comparison-like:

- **Centered narrow column** (`max-width: 760px; margin: 0 auto; width: 100%`, padding
  `space-8 space-4`) — used by **Setup** and **Settings**. Appropriate for any future page that is
  primarily a form or list, not a wide dataset.
- **Full-width with inner max-width** (`max-width: 1400px; margin: 0 auto` on inner rows, but the
  `<main>` itself has no max-width and uses `padding: space-6 space-4`) — used by **Run**. This lets
  the response-cards row scroll horizontally edge-to-edge while the header row above it still aligns
  to a readable width.

## Run screen: horizontal card row + sticky baseline

The response comparison is a flex row, not a CSS grid — `display:flex; gap:space-4; overflow-x:auto`.
Each response card is `flex:none; width:340px; min-height:260px`, so the row scrolls horizontally once
more than ~4 cards (2–5 possible) exceed viewport width, rather than wrapping or shrinking.

The baseline card (`index === 1`) is pinned via `position: sticky; left: 0; z-index: 1` with its own
`--color-surface` background and a directional shadow (`6px 0 12px -8px rgba(0,0,0,0.25)`) to separate
it from the scrolling cards behind it — this is intentional so the reference response stays visible
while comparing against the others. Preserve this sticky-first-column pattern in the real
implementation; it's load-bearing for the "compare against baseline" UX, not incidental mock styling.

## Grids

Only one CSS grid is used: Setup's Provider/Model row (`grid-template-columns: 1fr 1fr; gap:
space-4`). Everything else is flex. Don't reach for grid elsewhere without a specific reason — this
project's layout vocabulary is flex-first.

## Spacing rhythm between sections

Vertical rhythm inside a page is built purely from the `--space-*` scale on individual elements
(`margin-bottom`), not a stack/gap utility on the container — e.g. Setup's tag → h1 → p → grid → system
prompt field → prompt field → (warning) → run-count field → submit button each declare their own
`margin-bottom`. Keep this pattern (explicit margin per block) for consistency with the existing pages,
or introduce a `.stack` utility class in `styles.css` if/when a third form-like page is added and the
duplication becomes worth abstracting — per the incremental-modular approach, don't add that
abstraction preemptively.
