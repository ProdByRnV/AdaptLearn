import { useCallback, useRef, useState } from 'react'

/**
 * Small form state helper for the auth forms.
 *
 * - validate(values) returns {field: message} for every invalid field.
 * - Errors appear on submit. After that, a field with an error is re-checked as the learner types,
 *   so the message disappears as soon as it is fixed (and doesn't nag before the first submit).
 * - On a failed submit, focus moves to the first invalid field, which announces its message.
 * - onSubmit(values, {setErrors, setFormError}) runs once at a time; double submits are ignored.
 */
export function useForm({ initialValues, validate, onSubmit }) {
  const [values, setValues] = useState(initialValues)
  const [errors, setErrors] = useState({})
  const [formError, setFormError] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const submittingRef = useRef(false)
  const formRef = useRef(null)
  const fieldOrder = useRef(Object.keys(initialValues))

  const focusFirstError = useCallback((fieldErrors) => {
    const first = fieldOrder.current.find((name) => fieldErrors[name])
    if (first) formRef.current?.elements.namedItem(first)?.focus()
  }, [])

  const showErrors = useCallback(
    (fieldErrors) => {
      setErrors(fieldErrors)
      focusFirstError(fieldErrors)
    },
    [focusFirstError],
  )

  const handleChange = useCallback(
    (event) => {
      const { name, value } = event.target
      const next = { ...values, [name]: value }
      setValues(next)
      setErrors((current) => {
        if (Object.keys(current).length === 0) return current
        // Re-check only the fields already showing an error, against all the new values, so fixing
        // the password also clears a "passwords don't match" message.
        const fresh = validate(next)
        const updated = {}
        for (const field of Object.keys(current)) if (fresh[field]) updated[field] = fresh[field]
        return updated
      })
    },
    [values, validate],
  )

  const handleSubmit = useCallback(
    async (event) => {
      event.preventDefault()
      if (submittingRef.current) return
      setFormError(null)
      const fieldErrors = validate(values)
      if (Object.keys(fieldErrors).length > 0) {
        showErrors(fieldErrors)
        return
      }
      setErrors({})
      submittingRef.current = true
      setSubmitting(true)
      try {
        await onSubmit(values, { setErrors: showErrors, setFormError })
      } finally {
        submittingRef.current = false
        setSubmitting(false)
      }
    },
    [values, validate, onSubmit, showErrors],
  )

  return { values, errors, formError, submitting, formRef, handleChange, handleSubmit }
}
