import { useRouteError } from 'react-router'

import { FullPageError } from '@/components/common/ErrorState'

/** Shown when a page crashes while rendering, instead of a blank screen. */
export default function RouteError() {
  const error = useRouteError()
  if (import.meta.env.DEV) console.error(error)

  return (
    <FullPageError
      title="This page hit a problem"
      message="Reloading usually fixes it. If it keeps happening, go back to your home page."
      onRetry={() => window.location.reload()}
      retryLabel="Reload"
      action={
        <a href="/home" className="text-sm font-medium text-primary underline-offset-4 hover:underline">
          Go to home
        </a>
      }
    />
  )
}
