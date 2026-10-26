import { useCallback } from 'react'
import { Link } from 'react-router'

import { FormAlert } from '@/components/forms/FormAlert'
import { PasswordField } from '@/components/forms/PasswordField'
import { SubmitButton } from '@/components/forms/SubmitButton'
import { TextField } from '@/components/forms/TextField'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { useAuth } from '@/hooks/useAuth'
import { useForm } from '@/hooks/useForm'
import { serverErrorFeedback } from '@/lib/form-errors'
import { PASSWORD_MIN_CHARS, validateRegister } from '@/lib/validation'

const FIELDS = ['username', 'email', 'password']

export default function Register() {
  const { register } = useAuth()

  // On success the public-only route moves the new learner on to onboarding (US-01).
  const onSubmit = useCallback(
    async (values, { setErrors, setFormError }) => {
      try {
        await register({ username: values.username.trim(), email: values.email.trim(), password: values.password })
      } catch (error) {
        if (error?.response?.status === 409) {
          setErrors({ email: error.response.data?.detail || 'An account with this email already exists' })
          return
        }
        const { fieldErrors, formError } = serverErrorFeedback(error, FIELDS)
        setErrors(fieldErrors)
        setFormError(formError)
      }
    },
    [register],
  )

  const { values, errors, formError, submitting, formRef, handleChange, handleSubmit } = useForm({
    initialValues: { username: '', email: '', password: '', confirmPassword: '' },
    validate: validateRegister,
    onSubmit,
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xl text-ink">
          <h1>Create your account</h1>
        </CardTitle>
        <CardDescription>Your progress is saved to your account.</CardDescription>
      </CardHeader>
      <CardContent>
        <form ref={formRef} onSubmit={handleSubmit} noValidate className="flex flex-col gap-4" aria-label="Create account">
          <FormAlert message={formError} />
          <TextField
            label="Username"
            name="username"
            autoComplete="nickname"
            autoFocus
            hint="Shown on your dashboard."
            value={values.username}
            onChange={handleChange}
            error={errors.username}
          />
          <TextField
            label="Email"
            name="email"
            type="email"
            autoComplete="email"
            inputMode="email"
            value={values.email}
            onChange={handleChange}
            error={errors.email}
          />
          <PasswordField
            name="password"
            autoComplete="new-password"
            hint={`At least ${PASSWORD_MIN_CHARS} characters.`}
            value={values.password}
            onChange={handleChange}
            error={errors.password}
          />
          {/* There is no password reset yet, so a typo here would lock the learner out. */}
          <PasswordField
            label="Confirm password"
            name="confirmPassword"
            autoComplete="new-password"
            value={values.confirmPassword}
            onChange={handleChange}
            error={errors.confirmPassword}
          />
          <SubmitButton submitting={submitting} submittingLabel="Creating account…">
            Create account
          </SubmitButton>
        </form>
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
