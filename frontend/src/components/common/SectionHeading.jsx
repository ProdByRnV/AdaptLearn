/** A page section's heading with an optional hint underneath. */
export function SectionHeading({ id, title, hint }) {
  return (
    <div className="mb-3 flex flex-col gap-0.5">
      <h2 id={id} className="text-lg font-semibold text-ink">
        {title}
      </h2>
      {hint && <p className="text-sm text-muted-foreground">{hint}</p>}
    </div>
  )
}
