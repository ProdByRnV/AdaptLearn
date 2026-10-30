import { Loader2, Plus } from 'lucide-react'
import { cn } from 'cn'

import { Button } from '@/components/ui/button'

/** Join a domain. While any join is in flight every Join button waits; the one in flight says so. */
export function JoinButton({ domain, joining, onJoin, className }) {
  const busy = joining === domain.id
  return (
    <Button
      className={cn('h-9', className)}
      onClick={() => onJoin(domain.id)}
      disabled={Boolean(joining)}
      aria-label={`Join ${domain.name}`}
    >
      {busy ? <Loader2 aria-hidden="true" className="animate-spin" /> : <Plus aria-hidden="true" />}
      {busy ? 'Joining…' : 'Join'}
    </Button>
  )
}
