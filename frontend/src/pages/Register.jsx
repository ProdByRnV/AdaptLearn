import { Link } from 'react-router'

import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'

export default function Register() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xl text-ink">
          <h1>Create your account</h1>
        </CardTitle>
        <CardDescription>Start with the topics you already know.</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="rounded-lg bg-muted px-3 py-2 text-sm text-body">The registration form is built in Phase 14.</p>
      </CardContent>
      <CardFooter className="text-sm text-body">
        Already have an account?&nbsp;
        <Link to="/login" className="font-medium text-primary underline-offset-4 hover:underline">
          Log in
        </Link>
      </CardFooter>
    </Card>
  )
}
