import { useState } from 'react'
import { Outlet } from 'react-router'

import { Navbar } from '@/components/layout/Navbar'

/**
 * The signed-in layout. Pages can switch on focus mode through the outlet context (the running
 * quiz does), which hides the navbar and gives the page the whole window.
 */
export function AppShell() {
  const [focusMode, setFocusMode] = useState(false)

  return (
    <div className="flex min-h-svh flex-col">
      {!focusMode && (
        <>
          <a
            href="#main"
            className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 focus:rounded-md focus:bg-card focus:px-3 focus:py-2 focus:text-sm focus:shadow"
          >
            Skip to content
          </a>
          <Navbar />
        </>
      )}
      <main id="main" className={focusMode ? 'flex w-full flex-1 flex-col' : 'mx-auto w-full max-w-6xl flex-1 px-4 py-8'}>
        <Outlet context={{ setFocusMode }} />
      </main>
    </div>
  )
}
