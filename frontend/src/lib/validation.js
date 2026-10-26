// Client-side checks that mirror the backend's rules (backend/schemas/auth.py), so most mistakes
// are caught before a request. The server still validates everything; its answers win.

export const USERNAME_MAX = 80
export const EMAIL_MAX = 255
export const PASSWORD_MIN_CHARS = 8
export const PASSWORD_MAX_BYTES = 72 // bcrypt's limit

// Deliberately loose: something@something.tld. Stricter rules are left to the server.
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const encoder = new TextEncoder()

/** Characters as Python counts them (code points), not UTF-16 units. */
export const charCount = (value) => [...value].length
export const byteLength = (value) => encoder.encode(value).length

function emailError(raw) {
  const email = raw.trim()
  if (!email) return 'Enter your email address'
  if (email.length > EMAIL_MAX) return `Email must be at most ${EMAIL_MAX} characters`
  if (!EMAIL_PATTERN.test(email)) return 'Enter a valid email address, like name@example.com'
  return null
}

function newPasswordError(password) {
  if (!password) return 'Enter a password'
  if (charCount(password) < PASSWORD_MIN_CHARS) return `Use at least ${PASSWORD_MIN_CHARS} characters`
  if (byteLength(password) > PASSWORD_MAX_BYTES) {
    return `Too long: passwords can be at most ${PASSWORD_MAX_BYTES} bytes (accented letters and emoji count as more than one)`
  }
  return null
}

function compact(errors) {
  return Object.fromEntries(Object.entries(errors).filter(([, message]) => message))
}

export function validateLogin({ email, password }) {
  return compact({
    email: emailError(email),
    password: password ? null : 'Enter your password',
  })
}

export function validateRegister({ username, email, password, confirmPassword }) {
  const name = username.trim()
  return compact({
    username: !name
      ? 'Enter a username'
      : charCount(name) > USERNAME_MAX
        ? `Username must be at most ${USERNAME_MAX} characters`
        : null,
    email: emailError(email),
    password: newPasswordError(password),
    confirmPassword: !confirmPassword
      ? 'Re-enter your password'
      : confirmPassword !== password
        ? "Passwords don't match"
        : null,
  })
}
