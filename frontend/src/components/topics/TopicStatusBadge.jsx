import { cn } from 'cn'

import { Badge } from '@/components/ui/badge'
import { TOPIC_STATUS } from '@/lib/topic-status'

export function TopicStatusBadge({ status, className }) {
  const meta = TOPIC_STATUS[status] ?? { label: status, badgeClass: 'bg-secondary text-secondary-foreground' }
  return <Badge className={cn(meta.badgeClass, className)}>{meta.label}</Badge>
}
