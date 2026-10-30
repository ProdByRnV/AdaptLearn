import { render, screen } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { expect, it, vi } from 'vitest'

import { fetchCurrentUser } from '@/api/auth'
import { tokenStorage } from '@/api/client'
import { AuthProvider } from '@/context/AuthProvider'
import { routes } from '@/router'
import { LEARNER } from '@/test/helpers'

vi.mock('@/api/auth', () => ({ fetchCurrentUser: vi.fn(), loginRequest: vi.fn(), registerRequest: vi.fn() }))
vi.mock('@/pages/GraphPage', () => ({
  DomainGraphPage: () => null,
  MapPage: () => {
    throw new Error('render failed')
  },
}))

it('a page that crashes shows the error screen instead of a blank page', async () => {
  vi.spyOn(console, 'error').mockImplementation(() => {})
  vi.spyOn(console, 'warn').mockImplementation(() => {})
  tokenStorage.set('jwt-123')
  fetchCurrentUser.mockResolvedValue(LEARNER)
  render(
    <AuthProvider>
      <RouterProvider router={createMemoryRouter(routes, { initialEntries: ['/map'] })} />
    </AuthProvider>,
  )
  expect(await screen.findByRole('heading', { name: 'This page hit a problem' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Reload' })).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Go to home' })).toHaveAttribute('href', '/home')
})
