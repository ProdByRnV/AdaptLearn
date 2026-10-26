import { AppShell } from '@/components/layout/AppShell'
import { AuthLayout } from '@/components/layout/AuthLayout'
import Dashboard from '@/pages/Dashboard'
import GraphPage from '@/pages/GraphPage'
import Login from '@/pages/Login'
import NotFound from '@/pages/NotFound'
import Onboarding from '@/pages/Onboarding'
import QuizPage from '@/pages/QuizPage'
import Register from '@/pages/Register'
import RouteError from '@/pages/RouteError'
import { PostAuthRedirect } from '@/routes/PostAuthRedirect'
import { ProtectedRoute } from '@/routes/ProtectedRoute'
import { PublicOnlyRoute } from '@/routes/PublicOnlyRoute'

// Route table (ARCHITECTURE section 18). Exported so tests can mount it in a memory router.
export const routes = [
  {
    errorElement: <RouteError />,
    children: [
      {
        element: <PublicOnlyRoute />,
        children: [
          {
            element: <AuthLayout />,
            children: [
              { path: '/login', element: <Login /> },
              { path: '/register', element: <Register /> },
            ],
          },
        ],
      },
      {
        element: <ProtectedRoute />,
        children: [
          { path: '/', element: <PostAuthRedirect /> },
          {
            element: <AppShell />,
            children: [
              { path: '/onboarding', element: <Onboarding /> },
              { path: '/dashboard', element: <Dashboard /> },
              { path: '/quiz/:topicId', element: <QuizPage /> },
              { path: '/graph', element: <GraphPage /> },
            ],
          },
        ],
      },
      { path: '*', element: <NotFound /> },
    ],
  },
]
