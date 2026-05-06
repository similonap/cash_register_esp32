import { Link, useNavigate } from '@tanstack/react-router'
import { useSupabaseAuth } from '../auth/supabase'

export default function Header() {
  const { isAuthenticated, logout } = useSupabaseAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate({ to: '/login' })
  }

  return (
    <header className="border-b border-gray-200 bg-white px-4 py-3">
      <nav className="mx-auto flex max-w-4xl items-center gap-6">
        <Link to="/" className="font-semibold text-gray-900 no-underline">
          Cash Register Admin
        </Link>
        <div className="flex gap-4 text-sm">
          <Link to="/" className="text-gray-600 hover:text-gray-900">
            Home
          </Link>
          <Link to="/about" className="text-gray-600 hover:text-gray-900">
            About
          </Link>
        </div>
        {isAuthenticated && (
          <button
            onClick={handleLogout}
            className="ml-auto text-sm text-gray-500 hover:text-gray-900"
          >
            Logout
          </button>
        )}
      </nav>
    </header>
  )
}
