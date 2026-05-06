import { HeadContent, Outlet, Scripts, createRootRoute, useLocation, useNavigate } from '@tanstack/react-router'
import { useEffect } from 'react'
import { TanStackRouterDevtoolsPanel } from '@tanstack/react-router-devtools'
import { TanStackDevtools } from '@tanstack/react-devtools'
import Footer from '../components/Footer'
import Header from '../components/Header'
import { SupabaseAuthProvider, useSupabaseAuth } from '../auth/supabase'

import appCss from '../styles.css?url'

export const Route = createRootRoute({
  head: () => ({
    meta: [
      { charSet: 'utf-8' },
      { name: 'viewport', content: 'width=device-width, initial-scale=1' },
      { title: 'Cash Register Admin' },
    ],
    links: [{ rel: 'stylesheet', href: appCss }],
  }),
  shellComponent: RootDocument,
  component: RootComponent,
})

function RootComponent() {
  return (
    <SupabaseAuthProvider>
      <Header />
      <AuthGuard />
      <Footer />
    </SupabaseAuthProvider>
  )
}

function AuthGuard() {
  const { isAuthenticated, isLoading } = useSupabaseAuth()
  const location = useLocation()
  const navigate = useNavigate()

  useEffect(() => {
    if (isLoading || location.pathname === '/login') return
    if (!isAuthenticated) {
      navigate({ to: '/login', search: { redirect: location.href } })
    }
  }, [isAuthenticated, isLoading, location.pathname])

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-gray-400">
        Loading...
      </div>
    )
  }

  return <Outlet />
}

function RootDocument({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <HeadContent />
      </head>
      <body className="min-h-screen bg-white text-gray-900 antialiased">
        {children}
        <TanStackDevtools
          config={{ position: 'bottom-right' }}
          plugins={[{ name: 'Tanstack Router', render: <TanStackRouterDevtoolsPanel /> }]}
        />
        <Scripts />
      </body>
    </html>
  )
}
