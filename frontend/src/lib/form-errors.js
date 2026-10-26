import { getErrorMessage } from '@/api/client'

/**
 * Turn a failed auth request into form feedback. The backend's 422 responses carry
 * {"errors": [{field, message}]}; messages for fields on this form go next to the field,
 * anything else becomes the form-level message.
 */
export function serverErrorFeedback(error, fields) {
  const data = error?.response?.data
  if (error?.response?.status === 422 && Array.isArray(data?.errors)) {
    const fieldErrors = {}
    for (const { field, message } of data.errors) {
      if (fields.includes(field) && !fieldErrors[field]) fieldErrors[field] = sentence(message)
    }
    if (Object.keys(fieldErrors).length > 0) return { fieldErrors, formError: null }
  }
  return { fieldErrors: {}, formError: getErrorMessage(error) }
}

// Pydantic messages start lower-case ("value is not a valid email address: ...").
function sentence(message) {
  return message ? message.charAt(0).toUpperCase() + message.slice(1) : message
}
