# Style Guide

Source of truth: [`mock/styles.css`](./mock/styles.css). This file documents every design token and
where it's used; when the two disagree, `styles.css` wins and this file should be updated to match.

## Fonts

Loaded from Google Fonts: `Barlow` (body) and `Barlow Condensed` (headings).

| Token | Value | Usage |
|---|---|---|
| `--font-heading` | `"Barlow Condensed", system-ui, sans-serif` | `h1`–`h6`, `.btn`, `.card-title`, `.dialog-title`, nav brand |
| `--font-heading-weight` | `600` | Applied wherever `--font-heading` is used |
| `--font-body` | `"Barlow", system-ui, sans-serif` | `body`, all running text |

Type scale (fixed px, no responsive scaling defined in the mock):

| Element | Size | Notes |
|---|---|---|
| `h1` | 42px | Page title (e.g. "Compare model consistency") |
| `h2` | 32px | Unused in current pages, reserved |
| `h3` | 25px | Section headers (e.g. "Saved system prompts") |
| `h4` | 20px | Reserved |
| `h5` | 16px | Reserved |
| `h6` | 13px | Uppercase, `0.08em` letter-spacing — eyebrow/label style |
| body | 15px | `body` default, `line-height: 1.55` |
| small text | 11–14px | Field labels (12px), inputs/buttons (14px), tags/meta (11px) |

Headings share `line-height: 1.12` and `letter-spacing: -0.015em`.

## Color

Base roles:

| Token | Value | Usage |
|---|---|---|
| `--color-bg` | `#f2f2f3` | Page background |
| `--color-surface` | `#e9e9ea` | Raised surfaces (inputs, baseline column background) |
| `--color-text` | `#1d1f20` | Default text; also the base for all `color-mix` opacity tricks |
| `--color-accent` | `#5980a6` | Primary brand color — links, primary buttons, focus rings, active radio/segment |
| `--color-accent-2` | `#728fab` | Secondary accent, currently only backing the `--color-accent-2-*` ramp |
| `--color-divider` | `color-mix(in srgb, #1d1f20 16%, transparent)` | Hairline borders everywhere |

Tonal ramps (100–900, generated on a shared OKLCH lightness scale so the same step reads as the same
visual weight across roles): `--color-neutral-*`, `--color-accent-*`, `--color-accent-2-*`. Used for:

- `tag-accent` / `tag-accent-2` / `tag-neutral`: `*-100` background + `*-800` text
- Diff highlight `<mark>`: `--color-accent-200` background, `--color-accent-800` text
- Prompt-too-long warning text: `--color-accent-800`
- Dialog backdrop: `--color-neutral-900` at 50% opacity

Opacity/muting is done via `color-mix(in srgb, var(--color-text) X%, transparent)` rather than a
separate gray token — e.g. `.text-muted` (55%), field labels (70%), table headers (60%), card meta (50%).

## Spacing

An 8-step scale, not a power-of-two grid — increments of `3.4px` (chosen so `--space-4` ≈ 4× the base
unit while staying on a shared rhythm):

| Token | Value |
|---|---|
| `--space-1` | 3.4px |
| `--space-2` | 6.8px |
| `--space-3` | 10.2px |
| `--space-4` | 13.6px |
| `--space-6` | 20.4px |
| `--space-8` | 27.2px |

Note steps 5 and 7 are intentionally absent — pick the nearest defined step rather than introducing
new ones.

## Radius & elevation

| Token | Value |
|---|---|
| `--radius-sm` | 2px |
| `--radius-md` | 4px — default for inputs, buttons, cards, tags |
| `--radius-lg` | 7px — dialogs |
| `--shadow-sm` | `0 1px 2px` ink-tinted at 14% |
| `--shadow-md` | `0 3px 10px` ink-tinted at 16% |
| `--shadow-lg` | `0 12px 32px` ink-tinted at 22%, used by `.dialog` |

## The "blueprint" skin

The component classes below (`.card`, `.btn`, `.input`, `.tag`, `.seg`, `.dialog`) are built as a
**normal, rounded, filled design system** first — then a final override block in `styles.css`
(`/* — blueprint frame — */`) reskins them for this project specifically:

- All corner radii are zeroed (`border-radius: 0`) — square edges everywhere.
- `.card` and `.dialog` lose their filled background and become transparent with a 1px hairline
  border (`var(--color-divider)`).
- `.btn` gets a hairline border too; `.btn-primary` borders in `--color-accent`; `.btn-ghost` stays
  borderless.
- Interactive/structural elements additionally get a `.blueprint` wrapper: four small `.corner`
  registration-mark ticks (`<i class="corner tl|tr|bl|br">`) drawn just outside each box, evoking a
  wireframe/schematic look. Applied to: the login card, both primary buttons, response cards, retry
  buttons, and library-prompt cards.

**This is the current visual treatment for LLMChat and should be treated as intentional, not a
placeholder** — the underlying token system supports a filled/rounded look too, but any new UI should
match the blueprint skin (square corners, transparent surfaces, hairline borders, corner ticks on
interactive/card elements) unless a redesign explicitly changes it.

## Accessibility notes (from spec NFRs)

- Focus is fully suppressed except `:focus-visible`, which draws a 2px solid `--color-accent` outline
  — every interactive element must keep this reachable via keyboard tabbing.
- Diff highlighting (`<mark>` with `--color-accent-200`/`--color-accent-800`) must meet WCAG contrast
  independent of the toggle state — verify contrast ratio when the accent ramp changes.
- No component in the mock currently guards against `prefers-reduced-motion`; see
  [`animations.md`](./animations.md) for the recommendation on implementing this.
