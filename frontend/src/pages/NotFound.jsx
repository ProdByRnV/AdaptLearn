import { Compass } from 'lucide-react'
import { Link } from 'react-router'

import { Button } from '@/components/ui/button'
import { useAuth } from '@/hooks/useAuth'

export default function NotFound() {
  const { isAuthenticated } = useAuth()

  return (
    <main className="flex min-h-svh flex-col items-center justify-center gap-3 px-4 text-center">
      <div className="flex size-12 items-center justify-center rounded-full bg-accent text-accent-foreground">
        <Compass aria-hidden="true" className="size-6" />
      </div>
      <p className="text-sm font-semibold text-primary">404</p>
      <h1 className="text-2xl font-semibold tracking-tight text-ink">Page not found</h1>
      <p className="max-w-sm text-sm text-body">The page you were looking for doesn't exist or has moved.</p>
      <Button asChild className="mt-2">
        <Link to={isAuthenticated ? '/dashboard' : '/login'}>{isAuthenticated ? 'Go to dashboard' : 'Go to login'}</Link>
      </Button>
    </main>
  )
}
