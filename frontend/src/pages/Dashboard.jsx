/**
 * src/pages/Dashboard.jsx - Overview dashboard.
 * Shows key stats (total invoices, revenue, customers, items)
 * and a list of the 5 most recent invoices.
 */

import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { FileText, Users, Package, DollarSign, Plus } from 'lucide-react'
import api from '../api'

/** Reusable stat card */
function StatCard({ icon: Icon, label, value, color }) {
  return (
    <div className="card flex items-center gap-4">
      <div className={`p-3 rounded-xl ${color}`}>
        <Icon size={22} className="text-white" />
      </div>
      <div>
        <p className="text-sm text-gray-500">{label}</p>
        <p className="text-2xl font-bold text-gray-800">{value}</p>
      </div>
    </div>
  )
}

/** Status badge element */
function Badge({ status }) {
  const cls = { draft: 'badge-draft', sent: 'badge-sent', paid: 'badge-paid' }
  return <span className={cls[status] || 'badge-draft'}>{status}</span>
}

export default function Dashboard() {
  const [report, setReport]   = useState(null)
  const [invoices, setInvoices] = useState([])
  const [customers, setCustomers] = useState([])
  const [items, setItems]     = useState([])

  useEffect(() => {
    // Load all data in parallel
    Promise.all([
      api.get('/reports/summary'),
      api.get('/invoices'),
      api.get('/customers'),
      api.get('/items'),
    ]).then(([r, inv, cust, itm]) => {
      setReport(r.data)
      setInvoices(inv.data.slice(0, 5))   // 5 most recent
      setCustomers(cust.data)
      setItems(itm.data)
    }).catch(() => {})
  }, [])

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Dashboard</h1>
          <p className="text-gray-500 text-sm">Welcome back</p>
        </div>
        <Link to="/invoices/new" className="btn-primary flex items-center gap-2">
          <Plus size={16} />
          New Invoice
        </Link>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={FileText}   label="Total Invoices"  value={report?.total_invoices ?? '—'}  color="bg-brand-600" />
        <StatCard icon={DollarSign} label="Total Revenue"   value={report ? `$${report.total_revenue.toLocaleString('en', {minimumFractionDigits:2})}` : '—'} color="bg-emerald-500" />
        <StatCard icon={Users}      label="Customers"       value={customers.length}              color="bg-violet-500" />
        <StatCard icon={Package}    label="Catalog Items"   value={items.length}                  color="bg-amber-500" />
      </div>

      {/* Recent invoices */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-gray-700">Recent Invoices</h2>
          <Link to="/invoices" className="text-sm text-brand-600 hover:underline">View all</Link>
        </div>
        {invoices.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-8">No invoices yet</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-500 border-b border-gray-100">
                <th className="text-left pb-2 font-medium">Invoice #</th>
                <th className="text-left pb-2 font-medium">Customer</th>
                <th className="text-left pb-2 font-medium">Date</th>
                <th className="text-right pb-2 font-medium">Total</th>
                <th className="text-right pb-2 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {invoices.map(inv => (
                <tr key={inv.id} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="py-2">
                    <Link to={`/invoices/${inv.id}`} className="text-brand-600 hover:underline font-medium">
                      {inv.invoice_number}
                    </Link>
                  </td>
                  <td className="py-2 text-gray-600">{inv.customer?.name}</td>
                  <td className="py-2 text-gray-500">{inv.invoice_date}</td>
                  <td className="py-2 text-right font-mono">
                    {inv.currency} {inv.invoice_total.toLocaleString('en', {minimumFractionDigits: 2})}
                  </td>
                  <td className="py-2 text-right"><Badge status={inv.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Top customers */}
      {report?.customer_activity?.length > 0 && (
        <div className="card">
          <h2 className="font-semibold text-gray-700 mb-4">Top Customers</h2>
          <div className="space-y-2">
            {report.customer_activity.slice(0, 5).map(c => (
              <div key={c.customer_id} className="flex justify-between text-sm">
                <span className="text-gray-700">{c.customer_name}</span>
                <span className="font-mono text-gray-600">
                  {c.invoice_count} inv · ${c.total_amount.toLocaleString('en', {minimumFractionDigits:2})}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
