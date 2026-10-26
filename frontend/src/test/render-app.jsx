import { render } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router'

import { AuthProvider } from '@/context/AuthProvider'
import { routes } from '@/router'

/** Mount the whole app (real routes and auth provider) at a URL or location object. */
export function renderAt(entry) {
  const router = createMemoryRouter(routes, { initialEntries: [entry] })
  const view = render(
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>,
  )
  return { router, ...view }
}
