/**
 * src/components/Layout.jsx - Main application shell.
 * Provides the blue sidebar navigation and the content area.
 * Renders child routes via <Outlet />.
 */

import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Users, Package, FileText,
  BarChart2, Settings, LogOut, FileCheck
} from 'lucide-react'

const NAV_ITEMS = [
  { to: '/',          label: 'Dashboard',  icon: LayoutDashboard },
  { to: '/invoices',  label: 'Invoices',   icon: FileText },
  { to: '/customers', label: 'Customers',  icon: Users },
  { to: '/items',     label: 'Items',      icon: Package },
  { to: '/reports',   label: 'Reports',    icon: BarChart2 },
  { to: '/settings',  label: 'Settings',   icon: Settings },
]

export default function Layout() {
  const navigate = useNavigate()

  /** Clear token and redirect to login */
  function handleLogout() {
    localStorage.removeItem('token')
    navigate('/login')
  }

  return (
    <div className="flex h-screen overflow-hidden">
      {/* ── Sidebar ──────────────────────────────────────────────── */}
      <aside className="w-56 flex flex-col bg-brand-900 text-white flex-shrink-0">
        {/* Brand header */}
        <div className="px-5 py-5 border-b border-brand-800">
          <div className="flex items-center gap-2">
            <FileCheck size={22} className="text-brand-300" />
            <span className="font-bold text-lg tracking-wide">BLS Invoice</span>
          </div>
          <p className="text-brand-400 text-xs mt-0.5">Bluelight Systems</p>
        </div>

        {/* Navigation links */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors
                ${isActive
                  ? 'bg-brand-700 text-white'
                  : 'text-brand-200 hover:bg-brand-800 hover:text-white'}`
              }
            >
              <Icon size={17} />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Logout button */}
        <div className="px-3 py-4 border-t border-brand-800">
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 w-full px-3 py-2 rounded-lg text-sm text-brand-300 hover:bg-brand-800 hover:text-white transition-colors"
          >
            <LogOut size={17} />
            Logout
          </button>
        </div>
      </aside>

      {/* ── Main content ─────────────────────────────────────────── */}
      <main className="flex-1 overflow-y-auto bg-gray-50">
        <div className="max-w-6xl mx-auto px-6 py-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
