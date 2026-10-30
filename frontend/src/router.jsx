import { AppShell } from '@/components/layout/AppShell'
import { AuthLayout } from '@/components/layout/AuthLayout'
import Dashboard from '@/pages/Dashboard'
import Domains from '@/pages/Domains'
import { DomainGraphPage, MapPage } from '@/pages/GraphPage'
import Home from '@/pages/Home'
import Login from '@/pages/Login'
import NotFound from '@/pages/NotFound'
import Onboarding from '@/pages/Onboarding'
import QuizPage from '@/pages/QuizPage'
import Register from '@/pages/Register'
import RouteError from '@/pages/RouteError'
import { PostAuthRedirect } from '@/routes/PostAuthRedirect'
import { ProtectedRoute } from '@/routes/ProtectedRoute'
import { PublicOnlyRoute } from '@/routes/PublicOnlyRoute'
import { Redirect } from '@/routes/Redirect'

// Route table (ARCHITECTURE section 18, with the domain pages of Phase 24). Exported so tests can
// mount it in a memory router.
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
              { path: '/home', element: <Home /> },
              { path: '/domains', element: <Domains /> },
              { path: '/domains/:domainId', element: <Dashboard /> },
              { path: '/domains/:domainId/graph', element: <DomainGraphPage /> },
              { path: '/domains/:domainId/onboarding', element: <Onboarding /> },
              { path: '/map', element: <MapPage /> },
              { path: '/quiz/:topicId', element: <QuizPage /> },
              // Pages from before there were several domains, so old links still land somewhere sensible.
              { path: '/dashboard', element: <Redirect to="/home" /> },
              { path: '/onboarding', element: <Redirect to="/domains" /> },
              { path: '/graph', element: <Redirect to="/map" keepQuery /> },
            ],
          },
        ],
      },
      { path: '*', element: <NotFound /> },
    ],
  },
]
