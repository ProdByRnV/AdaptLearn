import { Outlet } from 'react-router'

import { Logo } from '@/components/layout/Logo'

// Sign-in pages: the dark ink panel echoes the AdaptLearn.pdf cover (slate-900 with teal-200 text).
export function AuthLayout() {
  return (
    <div className="grid min-h-svh lg:grid-cols-2">
      <aside className="hidden flex-col justify-between bg-ink p-10 lg:flex">
        <Logo textClassName="text-white" />
        <div className="max-w-md">
          <p className="text-3xl font-semibold leading-tight tracking-tight text-white">
            Learn in the order that makes sense for you.
          </p>
          <p className="mt-4 text-accent-on-dark">
            AdaptLearn maps what you already know, unlocks topics as you master their prerequisites and
            checks your understanding with short AI-generated quizzes.
          </p>
        </div>
        <p className="text-sm text-slate-300">Knowledge graph · Bayesian Knowledge Tracing · AI quizzes</p>
      </aside>
      <main className="flex flex-col items-center justify-center px-4 py-10">
        <div className="mb-8 lg:hidden">
          <Logo />
        </div>
        <div className="w-full max-w-sm">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
