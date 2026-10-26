import { ChevronDown, LayoutDashboard, LogOut, Network } from 'lucide-react'
import { Link, NavLink, useNavigate } from 'react-router'
import { cn } from 'cn'

import { Logo } from '@/components/layout/Logo'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useAuth } from '@/hooks/useAuth'

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/graph', label: 'Knowledge graph', icon: Network },
]

function initials(name = '') {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  return (parts.length > 1 ? parts[0][0] + parts.at(-1)[0] : name.slice(0, 2)).toUpperCase() || '?'
}

export function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <header className="sticky top-0 z-40 border-b bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/80">
      <div className="mx-auto flex h-14 max-w-6xl items-center gap-4 px-4">
        <Link to="/dashboard" aria-label="AdaptLearn home" className="shrink-0 rounded-md">
          <Logo markClassName="size-7" textClassName="hidden sm:inline" />
        </Link>

        <nav aria-label="Main" className="flex items-center gap-1">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  'inline-flex h-8 items-center gap-2 rounded-lg px-2.5 text-sm font-medium transition-colors',
                  isActive ? 'bg-accent text-accent-foreground' : 'text-body hover:bg-muted hover:text-ink',
                )
              }
            >
              <Icon aria-hidden="true" className="size-4" />
              <span className="max-sm:sr-only">{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="ml-auto">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="h-9 gap-2 px-1.5" aria-label="Account menu">
                <span className="flex size-7 items-center justify-center rounded-full bg-ink text-xs font-semibold text-accent-on-dark">
                  {initials(user?.username)}
                </span>
                <span className="hidden max-w-40 truncate text-sm font-medium text-ink md:inline">{user?.username}</span>
                <ChevronDown aria-hidden="true" className="size-4 text-muted-foreground" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel className="flex flex-col gap-0.5">
                <span className="truncate font-medium text-ink">{user?.username}</span>
                <span className="truncate text-xs font-normal text-muted-foreground">{user?.email}</span>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onSelect={handleLogout}>
                <LogOut aria-hidden="true" />
                Log out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  )
}
