/**
 * src/App.jsx - Root application component.
 * Defines all client-side routes using React Router.
 * Protected routes require a valid JWT token in localStorage.
 */

import { Routes, Route, Navigate } from 'react-router-dom'
import Layout       from './components/Layout'
import Login        from './pages/Login'
import Dashboard    from './pages/Dashboard'
import Customers    from './pages/Customers'
import Items        from './pages/Items'
import Invoices     from './pages/Invoices'
import InvoiceCreate from './pages/InvoiceCreate'
import InvoiceView  from './pages/InvoiceView'
import Reports      from './pages/Reports'
import Settings     from './pages/Settings'

/** Guard: redirect to /login if no token is stored */
function RequireAuth({ children }) {
  return localStorage.getItem('token') ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/login" element={<Login />} />

      {/* Protected — all wrapped in the sidebar Layout */}
      <Route path="/" element={<RequireAuth><Layout /></RequireAuth>}>
        <Route index element={<Dashboard />} />
        <Route path="customers" element={<Customers />} />
        <Route path="items"     element={<Items />} />
        <Route path="invoices"              element={<Invoices />} />
        <Route path="invoices/new"          element={<InvoiceCreate />} />
        <Route path="invoices/:id"          element={<InvoiceView />} />
        <Route path="invoices/:id/edit"     element={<InvoiceCreate />} />
        <Route path="reports"   element={<Reports />} />
        <Route path="settings"  element={<Settings />} />
      </Route>

      {/* Catch-all → dashboard */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
