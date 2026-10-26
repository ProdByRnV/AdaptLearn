import { Clock } from 'lucide-react'
import { Link } from 'react-router'

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { useAuth } from '@/hooks/useAuth'

export default function Login() {
  const { sessionExpired } = useAuth()

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xl text-ink">
          <h1>Welcome back</h1>
        </CardTitle>
        <CardDescription>Log in to continue your learning path.</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {sessionExpired && (
          <Alert>
            <Clock aria-hidden="true" />
            <AlertTitle>Your session has expired</AlertTitle>
            <AlertDescription>Please log in again.</AlertDescription>
          </Alert>
        )}
        <p className="rounded-lg bg-muted px-3 py-2 text-sm text-body">The login form is built in Phase 14.</p>
      </CardContent>
      <CardFooter className="text-sm text-body">
        New to AdaptLearn?&nbsp;
        <Link to="/register" className="font-medium text-primary underline-offset-4 hover:underline">
          Create an account
        </Link>
      </CardFooter>
    </Card>
  )
}
