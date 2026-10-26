import { describe, expect, it } from 'vitest'

import { serverErrorFeedback } from '@/lib/form-errors'
import { byteLength, charCount, validateLogin, validateRegister } from '@/lib/validation'
import { httpError, networkError } from '@/test/helpers'

const valid = { username: 'Puja', email: 'puja@example.com', password: 'StrongPassword123', confirmPassword: 'StrongPassword123' }

describe('validateLogin', () => {
  it('accepts a normal login', () => {
    expect(validateLogin({ email: ' puja@example.com ', password: 'x' })).toEqual({})
  })

  it.each([
    ['', 'Enter your email address'],
    ['   ', 'Enter your email address'],
    ['puja', 'Enter a valid email address, like name@example.com'],
    ['puja@example', 'Enter a valid email address, like name@example.com'],
    ['pu ja@example.com', 'Enter a valid email address, like name@example.com'],
    [`${'a'.repeat(250)}@example.com`, 'Email must be at most 255 characters'],
  ])('email %j -> %s', (email, message) => {
    expect(validateLogin({ email, password: 'x' }).email).toBe(message)
  })

  it('only requires a password (no length rules for existing accounts)', () => {
    expect(validateLogin({ email: 'a@b.co', password: '' }).password).toBe('Enter your password')
    expect(validateLogin({ email: 'a@b.co', password: 'short' })).toEqual({})
  })
})

describe('validateRegister', () => {
  it('accepts a valid registration', () => {
    expect(validateRegister(valid)).toEqual({})
  })

  it('reports every empty field at once', () => {
    expect(validateRegister({ username: '', email: '', password: '', confirmPassword: '' })).toEqual({
      username: 'Enter a username',
      email: 'Enter your email address',
      password: 'Enter a password',
      confirmPassword: 'Re-enter your password',
    })
  })

  it('username: blank after trimming, and the 80-character limit counted like the server', () => {
    expect(validateRegister({ ...valid, username: '   ' }).username).toBe('Enter a username')
    expect(validateRegister({ ...valid, username: 'a'.repeat(80) }).username).toBeUndefined()
    expect(validateRegister({ ...valid, username: ` ${'a'.repeat(80)} ` }).username).toBeUndefined()
    expect(validateRegister({ ...valid, username: 'a'.repeat(81) }).username).toBe('Username must be at most 80 characters')
    // 80 emoji are 160 UTF-16 units but 80 characters for the server.
    expect(validateRegister({ ...valid, username: '😀'.repeat(80) }).username).toBeUndefined()
  })

  it.each([
    ['1234567', 'Use at least 8 characters'],
    ['12345678', undefined],
    ['a'.repeat(72), undefined],
    ['a'.repeat(73), expect.stringMatching(/at most 72 bytes/)],
    // 37 accented letters: 37 characters but 74 bytes.
    ['é'.repeat(37), expect.stringMatching(/at most 72 bytes/)],
    // 8 emoji count as 8 characters, not 16.
    ['😀'.repeat(8), undefined],
    ['😀'.repeat(7), 'Use at least 8 characters'],
  ])('password %j', (password, expected) => {
    expect(validateRegister({ ...valid, password, confirmPassword: password }).password).toEqual(expected)
  })

  it('passwords must match exactly (no trimming)', () => {
    expect(validateRegister({ ...valid, confirmPassword: 'StrongPassword124' }).confirmPassword).toBe("Passwords don't match")
    expect(validateRegister({ ...valid, confirmPassword: 'StrongPassword123 ' }).confirmPassword).toBe("Passwords don't match")
  })

  it('counts like Python', () => {
    expect(charCount('😀é')).toBe(2)
    expect(byteLength('😀é')).toBe(6)
  })
})

describe('serverErrorFeedback', () => {
  it('puts 422 field messages next to the fields on the form', () => {
    const error = httpError(422, 'email: value is not a valid email address')
    error.response.data.errors = [
      { field: 'email', message: 'value is not a valid email address: The domain name x.invalid does not exist.' },
    ]
    expect(serverErrorFeedback(error, ['email', 'password'])).toEqual({
      fieldErrors: { email: 'Value is not a valid email address: The domain name x.invalid does not exist.' },
      formError: null,
    })
  })

  it('uses the form-level message for 422s about fields not on the form', () => {
    const error = httpError(422, 'request: Field required')
    error.response.data.errors = [{ field: 'request', message: 'Field required' }]
    expect(serverErrorFeedback(error, ['email'])).toEqual({ fieldErrors: {}, formError: 'request: Field required' })
  })

  it('uses the server message or a plain-language one otherwise', () => {
    expect(serverErrorFeedback(httpError(401, 'Incorrect email or password'), ['email']).formError).toBe(
      'Incorrect email or password',
    )
    expect(serverErrorFeedback(networkError(), ['email']).formError).toMatch(/can't reach/i)
  })
})
