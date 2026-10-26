import { Clock } from 'lucide-react'
import { useCallback } from 'react'
import { Link } from 'react-router'

import { FormAlert } from '@/components/forms/FormAlert'
import { PasswordField } from '@/components/forms/PasswordField'
import { SubmitButton } from '@/components/forms/SubmitButton'
import { TextField } from '@/components/forms/TextField'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { useAuth } from '@/hooks/useAuth'
import { useForm } from '@/hooks/useForm'
import { serverErrorFeedback } from '@/lib/form-errors'
import { validateLogin } from '@/lib/validation'

const FIELDS = ['email', 'password']

export default function Login() {
  const { login, sessionExpired } = useAuth()

  // On success the public-only route moves the learner on (remembered page, onboarding or dashboard).
  const onSubmit = useCallback(
    async (values, { setErrors, setFormError }) => {
      try {
        await login({ email: values.email.trim(), password: values.password })
      } catch (error) {
        const { fieldErrors, formError } = serverErrorFeedback(error, FIELDS)
        setErrors(fieldErrors)
        setFormError(formError)
      }
    },
    [login],
  )

  const { values, errors, formError, submitting, formRef, handleChange, handleSubmit } = useForm({
    initialValues: { email: '', password: '' },
    validate: validateLogin,
    onSubmit,
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xl text-ink">
          <h1>Welcome back</h1>
        </CardTitle>
        <CardDescription>Log in to continue your learning path.</CardDescription>
      </CardHeader>
      <CardContent>
        <form ref={formRef} onSubmit={handleSubmit} noValidate className="flex flex-col gap-4" aria-label="Log in">
          {sessionExpired && !formError && (
            <Alert>
              <Clock aria-hidden="true" />
              <AlertTitle>Your session has expired</AlertTitle>
              <AlertDescription>Please log in again.</AlertDescription>
            </Alert>
          )}
          <FormAlert message={formError} />
          <TextField
            label="Email"
            name="email"
            type="email"
            autoComplete="email"
            inputMode="email"
            autoFocus
            value={values.email}
            onChange={handleChange}
            error={errors.email}
          />
          <PasswordField
            name="password"
            autoComplete="current-password"
            value={values.password}
            onChange={handleChange}
            error={errors.password}
          />
          <SubmitButton submitting={submitting} submittingLabel="Logging in…">
            Log in
          </SubmitButton>
        </form>
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
