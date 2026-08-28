/**
 * The four registration ticks of the blueprint skin (docs/frontend/style-guide.md).
 *
 * Always rendered *alongside* the semantic component class, never instead of it:
 * `<div className="card blueprint"><BlueprintCorners />…</div>`. The ticks are
 * decorative, so they stay as empty `<i>` elements with no text or ARIA role.
 */
export function BlueprintCorners() {
  return (
    <>
      <i className="corner tl" />
      <i className="corner tr" />
      <i className="corner bl" />
      <i className="corner br" />
    </>
  );
}
