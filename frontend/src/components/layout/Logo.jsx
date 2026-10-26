import { cn } from 'cn'

// Three connected topics: the knowledge-graph mark (same drawing as public/favicon.svg).
export function LogoMark({ className }) {
  return (
    <svg viewBox="0 0 32 32" aria-hidden="true" className={cn('size-8', className)}>
      <rect width="32" height="32" rx="8" fill="var(--primary)" />
      <path d="M10 22 16 10l6 12M10 22h12" fill="none" stroke="var(--accent-on-dark)" strokeWidth="2" strokeLinecap="round" />
      <circle cx="16" cy="10" r="3" fill="#fff" />
      <circle cx="10" cy="22" r="3" fill="#fff" />
      <circle cx="22" cy="22" r="3" fill="var(--status-in-progress)" />
    </svg>
  )
}

export function Logo({ className, markClassName, textClassName }) {
  return (
    <span className={cn('inline-flex items-center gap-2', className)}>
      <LogoMark className={markClassName} />
      <span className={cn('text-lg font-semibold tracking-tight text-ink', textClassName)}>AdaptLearn</span>
    </span>
  )
}
