# Components

Source of truth: the component classes in [`mock/styles.css`](./mock/styles.css) (search for the
`— name —` section comments), as used in [`mock/LLMChat Mockups.dc.html`](./mock/LLMChat%20Mockups.dc.html).
Every component below is plain CSS class + plain markup — no JS is required for their visual states
(checked/hover/focus are handled by CSS `:has()`/`:checked`/`:focus-visible`).

## Button — `.btn`

Base: inline-flex, centered, 6px icon gap, heading font, `14px`, `radius-md` (0 under the blueprint
skin), padding `space-2` / `1.2 × space-3`.

| Variant | Class | Style |
|---|---|---|
| Primary | `.btn-primary` | Filled `--color-accent`, text `--color-bg`; hover → `--color-accent-600`; active → `--color-accent-700` |
| Secondary | `.btn-secondary` | Hairline border, transparent fill; hover/active tint the ink at 7%/14% |
| Ghost | `.btn-ghost` | No border, accent-colored text, tight horizontal padding; used for "Log out" and inline links styled as buttons |
| Icon-only | `.btn-icon` | 36×36px square, no padding — combine with another variant |
| Block | `.btn-block` | `width: 100%`, `margin-top: space-2` — primary CTA on Login and Setup |

States: `:disabled` → 45% opacity, `not-allowed` cursor (used for the "Run prompt N times" button while
`promptTooLong`). Icons are inline SVGs, 13–14px, `stroke-width: 1.5`, `stroke="currentColor"`.

Under the blueprint skin, primary/interactive buttons wrap in `.blueprint` and render 4 corner ticks
(see [`style-guide.md`](./style-guide.md)).

## Form field — `.field`

A field is `<div class="field">` wrapping a `<label>` + one control. Label: 12px, muted (70% ink),
`margin-bottom: 5px`.

### Text input / textarea — `.input`

Single-line height 36px min, `6px 10px` padding, 14px text, surface background, hairline border.
`textarea.input` sets `min-height: 90px` and `resize: vertical`. States: hover darkens the border to
45% ink; `:focus-visible` swaps the border to `--color-accent` with no outline offset gap.

Used for: email, password, model `<select>` (styled identically to `.input`), system prompt textarea,
prompt textarea, max-length number input.

### Radio — `.radio`

Custom dot: 16×16px circle, hairline border, hidden native `<input>` (visually hidden but present for
a11y/keyboard). Checked → filled `--color-accent` with a `--color-bg` ring inset (`box-shadow: inset 0
0 0 4px var(--color-bg)`). Not currently used in the four pages (reserved for future forms) — the
mockup uses `.seg` for all provider/count/phase/diff choices instead.

### Segmented control — `.seg` / `.seg-opt`

A `role="radiogroup"` of hairline-divided options; each `.seg-opt` wraps a visually-hidden radio
`<input>`. Selected option (`:has(input:checked)`) gets filled `--color-accent` background + `--color-bg`
text. Unselected options tint on hover. Focus-visible on the hidden input draws an inset 2px accent
outline on the whole option.

Used for: Provider (OpenAI/Anthropic), Number of runs (2–5), and the two run-screen demo controls
(phase, diff on/off).

## Card — `.card`

Flex column, `space-2` gap, `space-3` padding, `radius-md` (blueprint skin: transparent bg + hairline
border, square corners). Sub-parts:

- `.card-kicker` — 10px uppercase accent-colored eyebrow
- `.card-title` — heading font, 17px
- `.card-body` — 13px, 80% opacity, `flex: 1` (fills remaining card height)
- `.card-meta` — 11px, 50% ink, flex row with `space-2` gap (for icon + text pairs)

Elevation utilities `.elev-sm/md/lg` map to the shadow tokens — not used by default under the flat
blueprint skin, available if a card needs to visually lift (e.g. a dropdown menu or hover state).

Used for: the Login card, each response column on the Run screen, each saved-prompt row in Settings.

## Tag — `.tag`

Inline-flex pill, 11px text, `3px 10px` padding, `radius-md × 0.75`.

| Variant | Class | Meaning / usage |
|---|---|---|
| Accent | `.tag-accent` | Provider·model badge on Run screen; "Complete" status; provider connection status in Settings |
| Accent-2 | `.tag-accent-2` | Reserved, not currently used in the four pages |
| Neutral | `.tag-neutral` | "Queued" and "Failed" status |
| Outline | `.tag-outline` | Section eyebrow ("New run", "Settings"); "Baseline" badge; "Running"/"Retrying" status |

Status tags pair with an 11×11px inline SVG icon (clock = queued, spinner = running/retrying, check =
complete, warning triangle = failed) — see [`states.md`](./states.md) for the full status→tag→icon
mapping.

## Navigation — `.nav`

Flex row, `space-3`/`space-4` padding, no bottom border by default (the app shell adds one explicitly:
`border-bottom: 1px solid var(--color-divider)`). `.nav-brand` (heading font, 18px) sits left with
`margin-right: auto` pushing links right. Plain links (`.nav a`) turn accent-colored on hover or when
`aria-current="page"`.

## Table — `.table`

Standard `border-collapse` table; header cells are 11px uppercase muted labels with a bottom hairline;
body cells get a lighter 8%-ink bottom hairline; row hover tints the ink at 4%. **Not used by any of
the four current pages** — reserved for a future dense-data view (e.g. a run history list, if that
requirement ever changes from "ephemeral only").

## Dialog — `.dialog`

`.dialog-backdrop` is a fixed, centered overlay (`--color-neutral-900` at 50%). `.dialog` itself is
`min(440px, 100%)` wide, `radius-lg`, `shadow-lg`, `space-4` padding, with `.dialog-title` (20px
heading), `.dialog-body` (14px, 85% opacity), and `.dialog-actions` (right-aligned button row). **Not
used by any of the four current pages** — reserved for future confirmation flows (e.g. confirming
logout while a run is in progress, or a "delete saved prompt" confirmation).

## Skeleton / loading bars — `.llm-shimmer`

Not a token-file component — defined inline in the mock's `<style>` block since it's page-specific.
A `height`-only `<div>` with a shimmering gradient background, used to fake in-progress response text
(queued/running/retrying states). See [`animations.md`](./animations.md).

## Blueprint corner decoration — `.blueprint` / `.corner`

A structural, non-visual-only decorator: a `position: relative` wrapper plus four `<i class="corner
tl|tr|bl|br">` elements that draw small L-shaped registration ticks just outside the box edges. Always
added alongside — never instead of — the semantic component class (e.g. `class="card blueprint"`).
Required corner markup:

```html
<div class="card blueprint">
  <i class="corner tl"></i><i class="corner tr"></i><i class="corner bl"></i><i class="corner br"></i>
  ...
</div>
```
