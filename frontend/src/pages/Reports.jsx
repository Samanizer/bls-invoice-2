/**
 * src/pages/Reports.jsx - Business activity reports.
 * Displays:
 *  - Overall summary stats
 *  - Customer activity table (invoices count + total revenue per customer)
 *  - Item activity table (usage count + total revenue per item)
 */

import { useEffect, useState } from 'react'
import { BarChart2, Users, Package, DollarSign } from 'lucide-react'
import api from '../api'

function StatCard({ icon: Icon, label, value, color }) {
  return (
    <div className="card flex items-center gap-4">
      <div className={`p-3 rounded-xl ${color}`}><Icon size={20} className="text-white" /></div>
      <div>
        <p className="text-xs text-gray-500">{label}</p>
        <p className="text-xl font-bold text-gray-800">{value}</p>
      </div>
    </div>
  )
}

export default function Reports() {
  const [report, setReport] = useState(null)

  useEffect(() => {
    api.get('/reports/summary').then(r => setReport(r.data)).catch(() => {})
  }, [])

  if (!report) return <div className="text-gray-400 text-center py-20">Loading…</div>

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">Reports</h1>

      {/* Summary stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={BarChart2}  label="Total Invoices"     value={report.total_invoices} color="bg-brand-600" />
        <StatCard icon={DollarSign} label="Total Revenue (USD)" value={`$${report.total_revenue.toLocaleString('en',{minimumFractionDigits:2})}`} color="bg-emerald-500" />
        <StatCard icon={Users}      label="Active Customers"    value={report.customer_activity.length} color="bg-violet-500" />
        <StatCard icon={Package}    label="Items Used"          value={report.item_activity.length}     color="bg-amber-500" />
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Customer activity */}
        <div className="card">
          <h2 className="font-semibold text-gray-700 mb-4">Customer Activity</h2>
          {report.customer_activity.length === 0 ? (
            <p className="text-gray-400 text-sm text-center py-6">No data yet</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-500 border-b border-gray-100 text-xs">
                  <th className="text-left pb-2 font-medium">Customer</th>
                  <th className="text-right pb-2 font-medium">Invoices</th>
                  <th className="text-right pb-2 font-medium">Total (USD)</th>
                </tr>
              </thead>
              <tbody>
                {report.customer_activity.map(c => (
                  <tr key={c.customer_id} className="border-b border-gray-50">
                    <td className="py-2 text-gray-700">{c.customer_name}</td>
                    <td className="py-2 text-right text-gray-500">{c.invoice_count}</td>
                    <td className="py-2 text-right font-mono text-gray-800">
                      {c.total_amount.toLocaleString('en',{minimumFractionDigits:2})}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Item activity */}
        <div className="card">
          <h2 className="font-semibold text-gray-700 mb-4">Item Activity</h2>
          {report.item_activity.length === 0 ? (
            <p className="text-gray-400 text-sm text-center py-6">No data yet</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-500 border-b border-gray-100 text-xs">
                  <th className="text-left pb-2 font-medium">Item Code</th>
                  <th className="text-right pb-2 font-medium">Used</th>
                  <th className="text-right pb-2 font-medium">Qty</th>
                  <th className="text-right pb-2 font-medium">Total (USD)</th>
                </tr>
              </thead>
              <tbody>
                {report.item_activity.map(i => (
                  <tr key={i.item_code} className="border-b border-gray-50">
                    <td className="py-2 font-mono text-gray-700">{i.item_code}</td>
                    <td className="py-2 text-right text-gray-500">{i.times_used}</td>
                    <td className="py-2 text-right text-gray-500">{i.total_quantity}</td>
                    <td className="py-2 text-right font-mono text-gray-800">
                      {i.total_amount.toLocaleString('en',{minimumFractionDigits:2})}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}
