import { Check, ChevronsUpDown, LayoutGrid } from 'lucide-react'
import { Link } from 'react-router'

import { fetchCatalogue } from '@/api/domains'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useApiData } from '@/hooks/useApiData'
import { formatPercent } from '@/lib/format'
import { domainPath } from '@/lib/domains'

/**
 * Moves between the learner's joined domains, staying on the same view (dashboard or graph). The
 * current domain is always listed, joined or not, and the catalogue is one item away.
 */
export function DomainSwitcher({ domainId, name, view }) {
  const { data, error, loading } = useApiData(fetchCatalogue)
  const domains = (data?.domains ?? []).filter((d) => d.joined || d.id === domainId)

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        {/* The visible name is part of the accessible name (WCAG 2.5.3). */}
        <Button variant="outline" className="h-9 max-w-64" aria-label={`${name}: switch domain`}>
          <span className="truncate">{name}</span>
          <ChevronsUpDown aria-hidden="true" className="text-muted-foreground" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-64">
        <DropdownMenuLabel className="text-xs font-medium text-muted-foreground">Your domains</DropdownMenuLabel>
        {loading && <DropdownMenuItem disabled>Loading your domains…</DropdownMenuItem>}
        {error && <DropdownMenuItem disabled>Couldn't load your domains</DropdownMenuItem>}
        {domains.map((domain) => (
          <DropdownMenuItem key={domain.id} asChild>
            <Link to={domainPath(domain.id, view)} aria-current={domain.id === domainId ? 'page' : undefined}>
              <Check aria-hidden="true" className={domain.id === domainId ? 'text-primary' : 'invisible'} />
              <span className="flex-1 truncate">{domain.name}</span>
              <span className="text-xs text-muted-foreground tabular-nums">{formatPercent(domain.progress_percent)}</span>
            </Link>
          </DropdownMenuItem>
        ))}
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <Link to="/domains">
            <LayoutGrid aria-hidden="true" />
            Browse all domains
          </Link>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
