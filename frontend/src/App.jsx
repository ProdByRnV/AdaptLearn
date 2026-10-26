import { createBrowserRouter, RouterProvider } from 'react-router'

import { AuthProvider } from '@/context/AuthProvider'
import { routes } from '@/router'

const router = createBrowserRouter(routes)

export default function App() {
  return (
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  )
}
