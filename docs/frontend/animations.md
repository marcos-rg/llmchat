# Animations

Source of truth: the `@keyframes` block inside the `<helmet><style>` of
[`mock/LLMChat Mockups.dc.html`](./mock/LLMChat%20Mockups.dc.html) — kept page-local rather than in
`styles.css` since both are specific to the async-response-loading UI, not general design tokens.

## Defined keyframes

```css
@keyframes spin { to { transform: rotate(360deg); } }
@keyframes shimmer { 0% { background-position: -200px 0; } 100% { background-position: 200px 0; } }

.llm-spin { animation: spin 1s linear infinite; }
.llm-shimmer {
  background: linear-gradient(90deg, var(--color-neutral-200) 0%, var(--color-neutral-100) 50%, var(--color-neutral-200) 100%);
  background-size: 200px 100%;
  animation: shimmer 1.4s ease-in-out infinite;
}
```

| Animation | Applied to | Meaning |
|---|---|---|
| `.llm-spin` | The status-icon SVG on `running` and `retrying` response cards | In-progress LLM call |
| `.llm-shimmer` | Placeholder text bars on `queued`, `running`, and `retrying` response cards | Content not yet available — see [`states.md`](./states.md) for exact bar counts/widths per status |

These are the **only** animations in the mock — no page-transition, hover-lift, or entrance animation
exists anywhere else in the four screens. Don't add motion beyond this pair without a specific reason;
the visual language elsewhere (blueprint skin, hairline borders) is intentionally static/schematic.

## Accessibility: `prefers-reduced-motion`

Not implemented in the mock (it's a static HTML/CSS demo, not the production app), but required by the
spec's accessibility NFR. When implementing for real:

```css
@media (prefers-reduced-motion: reduce) {
  .llm-spin { animation: none; }
  .llm-shimmer { animation: none; background-position: 0 0; }
}
```

The spinner and shimmer both convey "in progress" purely through motion — when motion is disabled,
keep the static tag label ("Running"/"Retrying"/"Queued") as the sole indicator rather than substituting
a different visual, so the status semantics in `states.md` still hold.
